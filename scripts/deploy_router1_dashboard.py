#!/usr/bin/env python3
"""
Скрипт для быстрого развертывания дашборда мониторинга router1
Использует FastAPI сервис для создания дашборда в Grafana
"""

import requests
import json
import sys
from datetime import datetime

class Router1DashboardDeployer:
    def __init__(self, api_base_url="http://dashboards-service.localhost:8050"):
        self.api_base_url = api_base_url
        
    def create_router1_dashboard(self):
        """Создает дашборд для мониторинга router1"""
        
        dashboard_data = {
            "dashboard": {
                "title": "Router1 Network Monitoring",
                "description": "Comprehensive monitoring dashboard for Router1 network metrics",
                "tags": ["router1", "network", "monitoring", "production"],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 1,
                "refresh": "30s",
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Interface Traffic (In/Out)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "rate(ifInOctets{instance=\"router1\",ifDescr!~\".*Loopback.*\"}[5m])*8",
                                "legendFormat": "{{ifDescr}} In (bps)"
                            },
                            {
                                "expr": "rate(ifOutOctets{instance=\"router1\",ifDescr!~\".*Loopback.*\"}[5m])*8",
                                "legendFormat": "{{ifDescr}} Out (bps)"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "CPU Utilization",
                        "type": "singlestat",
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "avg(cpu_usage{instance=\"router1\"})",
                                "legendFormat": "CPU %"
                            }
                        ],
                        "thresholds": [80, 60]
                    },
                    {
                        "id": 3,
                        "title": "Memory Utilization",
                        "type": "singlestat",
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "memory_usage{instance=\"router1\"}",
                                "legendFormat": "Memory %"
                            }
                        ],
                        "thresholds": [85, 70]
                    },
                    {
                        "id": 4,
                        "title": "Interface Status",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "ifOperStatus{instance=\"router1\"}",
                                "legendFormat": "{{ifDescr}}"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Interface Errors",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "rate(ifInErrors{instance=\"router1\"}[5m])",
                                "legendFormat": "{{ifDescr}} In Errors/sec"
                            },
                            {
                                "expr": "rate(ifOutErrors{instance=\"router1\"}[5m])",
                                "legendFormat": "{{ifDescr}} Out Errors/sec"
                            }
                        ]
                    },
                    {
                        "id": 6,
                        "title": "Device Uptime",
                        "type": "singlestat",
                        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 12},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "sysUpTime{instance=\"router1\"}/100",
                                "legendFormat": "Uptime"
                            }
                        ]
                    },
                    {
                        "id": 7,
                        "title": "ICMP Ping Response",
                        "type": "graph",
                        "gridPos": {"h": 4, "w": 6, "x": 18, "y": 12},
                        "datasource": {"type": "prometheus"},
                        "targets": [
                            {
                                "expr": "probe_success{instance=\"router1\"}",
                                "legendFormat": "Ping Success"
                            },
                            {
                                "expr": "probe_duration_seconds{instance=\"router1\"}*1000",
                                "legendFormat": "Response Time (ms)"
                            }
                        ]
                    }
                ]
            },
            "folderId": 0,
            "overwrite": True,
            "message": f"Router1 monitoring dashboard created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        return dashboard_data
    
    def deploy(self):
        """Развертывает дашборд router1"""
        print("🚀 Развертывание дашборда мониторинга Router1")
        print("=" * 50)
        
        # Проверка доступности API
        print("1. Проверка доступности API...")
        try:
            health_response = requests.get(f"{self.api_base_url}/healthz", timeout=5)
            if health_response.status_code == 200:
                print("   ✅ API доступен")
            else:
                print(f"   ❌ API недоступен (статус: {health_response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка подключения к API: {e}")
            return False
        
        # Создание дашборда
        print("2. Создание дашборда...")
        try:
            dashboard_data = self.create_router1_dashboard()
            response = requests.post(
                f"{self.api_base_url}/dashboards/",
                json=dashboard_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                uid = result.get('uid')
                dashboard_id = result.get('id')
                url = result.get('url', '')
                
                print("   ✅ Дашборд успешно создан!")
                print(f"   📊 UID: {uid}")
                print(f"   🆔 ID: {dashboard_id}")
                print(f"   🔗 URL: http://grafana.localhost:3001{url}")
                
                # Дополнительная проверка
                print("3. Проверка созданного дашборда...")
                try:
                    check_response = requests.get(f"{self.api_base_url}/dashboards/{uid}", timeout=10)
                    if check_response.status_code == 200:
                        dashboard_info = check_response.json()
                        title = dashboard_info.get('dashboard', {}).get('title', 'N/A')
                        panels_count = len(dashboard_info.get('dashboard', {}).get('panels', []))
                        print(f"   ✅ Дашборд проверен: '{title}' с {panels_count} панелями")
                    else:
                        print("   ⚠️  Предупреждение: не удалось проверить созданный дашборд")
                except Exception as e:
                    print(f"   ⚠️  Предупреждение при проверке: {e}")
                
                return True
                
            else:
                print(f"   ❌ Ошибка создания дашборда (статус: {response.status_code})")
                print(f"   📄 Ответ: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при создании дашборда: {e}")
            return False
    
    def show_metrics_info(self):
        """Показывает информацию о метриках, которые должны быть доступны"""
        print("\n📊 ИНФОРМАЦИЯ О ТРЕБУЕМЫХ МЕТРИКАХ PROMETHEUS")
        print("=" * 50)
        print("Для корректной работы дашборда должны быть доступны следующие метрики:")
        print()
        print("🌐 Сетевые метрики:")
        print("  - ifInOctets{instance=\"router1\"}")
        print("  - ifOutOctets{instance=\"router1\"}")
        print("  - ifInErrors{instance=\"router1\"}")
        print("  - ifOutErrors{instance=\"router1\"}")
        print("  - ifOperStatus{instance=\"router1\"}")
        print()
        print("💻 Системные метрики:")
        print("  - cpu_usage{instance=\"router1\"}")
        print("  - memory_usage{instance=\"router1\"}")
        print("  - sysUpTime{instance=\"router1\"}")
        print()
        print("🔍 Мониторинг доступности:")
        print("  - probe_success{instance=\"router1\"}")
        print("  - probe_duration_seconds{instance=\"router1\"}")
        print()
        print("📝 Убедитесь, что SNMP Exporter и Blackbox Exporter настроены")
        print("   для сбора этих метрик с router1!")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        deployer = Router1DashboardDeployer()
        deployer.show_metrics_info()
        return
    
    deployer = Router1DashboardDeployer()
    
    success = deployer.deploy()
    
    if success:
        print("\n🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("\n📋 Следующие шаги:")
        print("1. Откройте Grafana: http://grafana.localhost:3001")
        print("2. Перейдите к созданному дашборду")
        print("3. Убедитесь, что метрики поступают от router1")
        print("4. При необходимости настройте алерты")
        deployer.show_metrics_info()
    else:
        print("\n❌ ОШИБКА РАЗВЕРТЫВАНИЯ!")
        print("Проверьте:")
        print("- Доступность FastAPI сервиса (http://dashboards-service.localhost:8050)")
        print("- Доступность Grafana (http://grafana.localhost:3001)")
        print("- Корректность настроек API ключа")
        sys.exit(1)

if __name__ == "__main__":
    main()
