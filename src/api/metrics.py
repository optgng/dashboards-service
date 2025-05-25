from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import httpx
import time
import os
import logging
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class GrafanaMetrics(BaseModel):
    total_dashboards: int
    total_panels: int
    api_response_time_ms: float
    grafana_health_status: bool

async def collect_grafana_metrics():
    """Собирает метрики с Grafana используя тот же подход что и GrafanaService"""
    
    # Используем настройки из конфига как в GrafanaService
    grafana_url = settings.get('grafana_url', 'http://grafana.localhost:3000')
    grafana_api_key = settings.get('grafana_api_key', '')
    
    headers = {
        "Authorization": f"Bearer {grafana_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    metrics = {
        "total_dashboards": 0,
        "total_panels": 0,
        "api_response_time_ms": 0.0,
        "grafana_health_status": False
    }
    
    timeout = httpx.Timeout(30.0)
    
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                # Проверка здоровья Grafana
                health_response = await client.get(
                    f"{grafana_url}/api/health",
                    headers=headers,
                    follow_redirects=False
                )
                
                # Если получили редирект, пробуем альтернативный endpoint
                if health_response.status_code in [307, 302, 301]:
                    logger.warning(f"Grafana redirected health check - trying admin stats: {health_response.status_code}")
                    health_response = await client.get(
                        f"{grafana_url}/api/admin/stats",
                        headers=headers,
                        follow_redirects=False
                    )
                
                if health_response.status_code == 200:
                    metrics["grafana_health_status"] = True
                    logger.info("Grafana health check passed")
                else:
                    logger.warning(f"Grafana health check failed: {health_response.status_code}")
                
                # Получение списка дашбордов
                dashboards_response = await client.get(
                    f"{grafana_url}/api/search",
                    headers=headers,
                    follow_redirects=False
                )
                
                end_time = time.time()
                api_response_time = (end_time - start_time) * 1000
                
                # Проверяем на редирект
                if dashboards_response.status_code in [307, 302, 301]:
                    logger.error("Grafana API requires authentication - check API key configuration")
                    logger.error(f"Redirect response: {dashboards_response.headers.get('location', 'No location header')}")
                    metrics["grafana_health_status"] = False
                    metrics["api_response_time_ms"] = round(api_response_time, 2)
                    return metrics
                
                if dashboards_response.status_code == 200:
                    try:
                        dashboards_data = dashboards_response.json()
                        metrics["total_dashboards"] = len(dashboards_data)
                        logger.info(f"Found {len(dashboards_data)} dashboards")
                        
                        # Подсчитываем общее количество панелей
                        total_panels = 0
                        for dashboard in dashboards_data:
                            if dashboard.get("type") == "dash-db":
                                try:
                                    dashboard_detail_response = await client.get(
                                        f"{grafana_url}/api/dashboards/uid/{dashboard['uid']}",
                                        headers=headers,
                                        follow_redirects=False
                                    )
                                    if dashboard_detail_response.status_code == 200:
                                        dashboard_detail = dashboard_detail_response.json()
                                        panels = dashboard_detail.get("dashboard", {}).get("panels", [])
                                        total_panels += len(panels)
                                except Exception as e:
                                    logger.warning(f"Failed to get panels for dashboard {dashboard.get('uid')}: {e}")
                                    continue
                        
                        metrics["total_panels"] = total_panels
                        logger.info(f"Total panels found: {total_panels}")
                        
                    except Exception as e:
                        logger.error(f"Failed to parse Grafana response: {e}")
                        logger.debug(f"Response content: {dashboards_response.text[:200]}")
                        metrics["grafana_health_status"] = False
                        
                else:
                    logger.error(f"Failed to get dashboards: {dashboards_response.status_code}")
                    logger.debug(f"Response: {dashboards_response.text[:200]}")
                    
                metrics["api_response_time_ms"] = round(api_response_time, 2)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                metrics["grafana_health_status"] = False
                metrics["api_response_time_ms"] = 0.0
            except httpx.ConnectError as e:
                logger.error(f"Connection error to Grafana at {grafana_url}: {e}")
                metrics["grafana_health_status"] = False
                metrics["api_response_time_ms"] = 0.0
                
    except Exception as e:
        logger.error(f"Unexpected error getting Grafana metrics: {e}")
        metrics["grafana_health_status"] = False
        metrics["api_response_time_ms"] = 0.0
    
    return metrics

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Возвращает метрики в формате Prometheus
    Использует тот же код сбора метрик что и JSON endpoint
    """
    # Используем ту же функцию что и для JSON
    metrics = await collect_grafana_metrics()
    
    prometheus_output = f"""# HELP grafana_dashboards_total Total number of dashboards in Grafana
# TYPE grafana_dashboards_total gauge
grafana_dashboards_total {metrics['total_dashboards']}

# HELP grafana_panels_total Total number of panels across all dashboards
# TYPE grafana_panels_total gauge
grafana_panels_total {metrics['total_panels']}

# HELP grafana_api_response_time_milliseconds API response time in milliseconds
# TYPE grafana_api_response_time_milliseconds gauge
grafana_api_response_time_milliseconds {metrics['api_response_time_ms']}

# HELP grafana_health_status Grafana health status (1 = healthy, 0 = unhealthy)
# TYPE grafana_health_status gauge
grafana_health_status {1 if metrics['grafana_health_status'] else 0}

# HELP dashboards_service_info Information about the dashboards service
# TYPE dashboards_service_info gauge
dashboards_service_info{{version="1.2.3",service="dashboards-service"}} 1
"""
    
    return prometheus_output

@router.get("/metrics/json", response_model=GrafanaMetrics)
async def get_metrics_json():
    """
    Возвращает метрики в формате JSON
    """
    metrics = await collect_grafana_metrics()
    return GrafanaMetrics(**metrics)

@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    Получает краткую сводку всех метрик в удобочитаемом формате
    """
    metrics = await collect_grafana_metrics()
    
    status_emoji = "✅" if metrics["grafana_health_status"] else "❌"
    
    # Добавляем диагностическую информацию используя settings
    grafana_url = settings.get('grafana_url', 'http://grafana.localhost:3000')
    grafana_api_key = settings.get('grafana_api_key', '')
    
    return {
        "summary": f"{status_emoji} Grafana Status",
        "details": {
            "dashboards_count": f"📊 {metrics['total_dashboards']} дашбордов",
            "panels_count": f"📈 {metrics['total_panels']} панелей",
            "response_time": f"⏱️ {metrics['api_response_time_ms']}ms",
            "health": f"{status_emoji} {'Доступна' if metrics['grafana_health_status'] else 'Недоступна'}"
        },
        "endpoints": {
            "prometheus": "/api/metrics",
            "json": "/api/metrics/json", 
            "summary": "/api/metrics/summary"
        },
        "diagnostics": {
            "grafana_url": grafana_url,
            "api_key_configured": bool(grafana_api_key),
            "api_key_length": len(grafana_api_key) if grafana_api_key else 0,
            "settings_source": "config.settings",
            "debug_info": "Metrics router working correctly"
        },
        "raw_metrics": metrics
    }
