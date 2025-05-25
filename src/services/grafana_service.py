from typing import List, Dict, Any, Optional
import httpx
import json
import asyncio
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from config import settings
import logging
from pydantic import BaseModel, ValidationError
from os import path

class GrafanaApiError(Exception):
    pass

class DashboardSchema(BaseModel):
    dashboard: Dict
    overwrite: bool = False

class GrafanaService:
    def __init__(self):
        self.base_url = settings.get('grafana_url', 'http://grafana.localhost:3000')  # Исправлен URL
        self.headers = {
            "Authorization": f"Bearer {settings.get('grafana_api_key')}",
            "Content-Type": "application/json",
        }
        self._cache = {}
        self.timeout = httpx.Timeout(30.0)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Общий метод для выполнения HTTP-запросов с обработкой ошибок"""
        kwargs['timeout'] = self.timeout
        
        logging.debug(f"Request to Grafana: method={method}, endpoint={endpoint}, kwargs={kwargs}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise GrafanaApiError(f"API error: {e.response.text}")
            except httpx.ConnectError:
                logging.error(f"Connection error to Grafana at {self.base_url}")
                raise GrafanaApiError(f"Failed to connect to Grafana at {self.base_url}")
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                raise GrafanaApiError(f"Request failed: {str(e)}")

    async def get_dashboards(self, tag: Optional[str] = None, limit: int = 100, search: Optional[str] = None) -> List[Dict]:
        """Получение списка дашбордов с поддержкой поиска и пагинации"""
        params = {"limit": limit}
        if tag:
            params["tag"] = tag
        if search:
            params["query"] = search
        
        try:
            result = await self._make_request("GET", "/api/search", params=params)
            return [self._parse_dashboard_metadata(item) for item in result]
        except Exception as e:
            raise GrafanaApiError(f"Failed to get dashboards: {str(e)}")

    async def get_dashboard(self, uid: str) -> Dict:
        """Получение полной информации о дашборде"""
        cache_key = f"dashboard_{uid}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await self._make_request("GET", f"/api/dashboards/uid/{uid}")
        self._cache[cache_key] = result
        return result

    async def create_dashboard(self, dashboard_data: Dict) -> Dict:
        """Создание нового дашборда"""
        try:
            validated_data = DashboardSchema(**dashboard_data)
        except ValidationError as e:
            raise GrafanaApiError(f"Invalid dashboard data: {e}")

        if "title" not in dashboard_data["dashboard"]:
            raise GrafanaApiError("Field 'title' is required in the dashboard data.")

        logging.debug(f"Dashboard title being returned: {dashboard_data['dashboard']['title']}")

        result = await self._make_request("POST", "/api/dashboards/db", json=validated_data.dict())
        
        # Логируем данные для отладки
        logging.debug(f"Grafana response: {result}")
        
        # Преобразуем ответ Grafana API в формат DashboardResponse
        response_data = {
            "id": result["id"],
            "uid": result["uid"],
            "title": dashboard_data["dashboard"]["title"],
            "url": result["url"],
            "version": result["version"]
        }
        logging.debug(f"Final response data: {response_data}")
        return response_data

    async def update_dashboard(self, uid: str, dashboard_data: Dict) -> Dict:
        """Обновление существующего дашборда"""
        current = await self.get_dashboard(uid)
        dashboard_data["dashboard"]["version"] = current["dashboard"]["version"]
        dashboard_data["dashboard"]["id"] = current["dashboard"]["id"]

        logging.debug(f"Updating dashboard with data: {dashboard_data}")

        try:
            validated_data = DashboardSchema(**dashboard_data)
        except ValidationError as e:
            raise GrafanaApiError(f"Invalid dashboard data: {e}")

        if "title" not in dashboard_data["dashboard"]:
            raise GrafanaApiError("Field 'title' is required in the dashboard data.")

        result = await self._make_request("POST", "/api/dashboards/db", json=validated_data.dict())

        # Преобразуем ответ Grafana API в формат DashboardResponse
        return {
            "id": result["id"],
            "uid": result["uid"],
            "title": dashboard_data["dashboard"]["title"],
            "url": result["url"],
            "version": result["version"]
        }

    async def export_dashboard(self, uid: str, output_dir: str = "exports") -> str:
        """Экспорт дашборда в JSON файл"""
        try:
            dashboard = await self.get_dashboard(uid)
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)

            filename = f"{dashboard['dashboard']['title']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, indent=2)

            return str(filepath)
        except Exception as e:
            logging.error(f"Failed to export dashboard {uid}: {e}")
            raise GrafanaApiError(f"Failed to export dashboard {uid}: {e}")

    async def import_dashboard(self, filepath: str) -> Dict:
        """Импорт дашборда из JSON файла"""
        if not path.exists(filepath):
            raise GrafanaApiError(f"File {filepath} does not exist")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dashboard_data = json.load(f)
            return await self.create_dashboard(dashboard_data)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from {filepath}: {e}")
            raise GrafanaApiError(f"Invalid JSON format in {filepath}: {e}")
        except Exception as e:
            logging.error(f"Failed to import dashboard from {filepath}: {e}")
            raise GrafanaApiError(f"Failed to import dashboard from {filepath}: {e}")

    async def compare_versions(self, uid: str, version1: int, version2: int) -> Dict:
        """Сравнение двух версий дашборда"""
        v1 = await self._make_request("GET", f"/api/dashboards/uid/{uid}/versions/{version1}")
        v2 = await self._make_request("GET", f"/api/dashboards/uid/{uid}/versions/{version2}")
        return {
            "additions": self._compare_dict(v1["dashboard"], v2["dashboard"]),
            "deletions": self._compare_dict(v2["dashboard"], v1["dashboard"])
        }

    def _compare_dict(self, d1: Dict, d2: Dict) -> Dict:
        """Утилита для сравнения словарей"""
        diff = {}
        for k, v in d1.items():
            if k not in d2:
                diff[k] = v
            elif isinstance(v, dict) and isinstance(d2[k], dict):
                nested_diff = self._compare_dict(v, d2[k])
                if nested_diff:
                    diff[k] = nested_diff
            elif v != d2[k]:
                diff[k] = v
        return diff

    def _parse_dashboard_metadata(self, data: Dict) -> Dict:
        """Парсинг метаданных дашборда"""
        return {
            "uid": data.get("uid", ""),
            "title": data.get("title", ""),
            "url": data.get("url", ""),
            "type": data.get("type", ""),
            "tags": data.get("tags", []),
            "isStarred": data.get("isStarred", False)
        }

    def visualize_dashboard(self, dashboard_data: Dict) -> str:
        """Создание текстового представления структуры дашборда"""
        output = []
        dash = dashboard_data.get("dashboard", {})
        
        output.append(f"Dashboard: {dash.get('title', 'Untitled')}")
        output.append("=" * 50)
        
        # Panels
        output.append("\nPanels:")
        for panel in dash.get("panels", []):
            output.append(f"  - {panel.get('title', 'Untitled Panel')} ({panel.get('type', 'unknown')})")
        
        # Variables
        if "templating" in dash:
            output.append("\nVariables:")
            for var in dash["templating"].get("list", []):
                output.append(f"  - {var.get('name')}: {var.get('type')}")
        
        return "\n".join(output)

    async def add_panel(self, dashboard_uid: str, panel_data: Dict) -> Dict:
        """Добавление новой панели на дашборд"""
        dashboard = await self.get_dashboard(dashboard_uid)
        dashboard_data = dashboard["dashboard"].copy()
        
        # Генерируем новый ID панели
        max_id = max([p.get("id", 0) for p in dashboard_data.get("panels", [])], default=0)
        panel_id = max_id + 1
        panel_data["id"] = panel_id
        
        # Добавляем панель
        if "panels" not in dashboard_data:
            dashboard_data["panels"] = []
        dashboard_data["panels"].append(panel_data)
        
        # Обновляем дашборд с сохранением версии и структуры
        update_data = {
            "dashboard": dashboard_data,
            "folderId": 0,
            "overwrite": True
        }
        
        await self.update_dashboard(dashboard_uid, update_data)
        
        # Очищаем кэш дашборда для обеспечения согласованности данных
        cache_key = f"dashboard_{dashboard_uid}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Возвращаем ID созданной панели
        return {"panel_id": panel_id}

    async def update_panel(self, dashboard_uid: str, panel_id: int, panel_data: Dict) -> Dict:
        """Обновление существующей панели"""
        dashboard = await self.get_dashboard(dashboard_uid)
        dashboard_data = dashboard["dashboard"].copy()
        
        # Ищем и обновляем панель
        panel_found = False
        for idx, panel in enumerate(dashboard_data.get("panels", [])):
            if panel.get("id") == panel_id:
                panel_data["id"] = panel_id  # Сохраняем ID панели
                dashboard_data["panels"][idx] = panel_data
                panel_found = True
                break
        
        if not panel_found:
            raise GrafanaApiError(f"Panel {panel_id} not found")
        
        # Обновляем дашборд с сохранением версии и структуры
        update_data = {
            "dashboard": dashboard_data,
            "folderId": 0,
            "overwrite": True
        }
        
        await self.update_dashboard(dashboard_uid, update_data)
        
        # Очищаем кэш дашборда для обеспечения согласованности данных
        cache_key = f"dashboard_{dashboard_uid}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        # Возвращаем обновленную панель
        return {"panel_id": panel_id, "updated": True}

    async def delete_panel(self, dashboard_uid: str, panel_id: int) -> None:
        """Удаление панели с дашборда"""
        dashboard = await self.get_dashboard(dashboard_uid)
        dashboard_data = dashboard["dashboard"].copy()
        
        # Проверяем, существует ли панель
        panel_exists = any(p.get("id") == panel_id for p in dashboard_data.get("panels", []))
        if not panel_exists:
            raise GrafanaApiError(f"Panel {panel_id} not found")
        
        # Удаляем панель
        dashboard_data["panels"] = [
            p for p in dashboard_data.get("panels", [])
            if p.get("id") != panel_id
        ]
        
        # Обновляем дашборд с сохранением версии и структуры
        update_data = {
            "dashboard": dashboard_data,
            "folderId": 0,
            "overwrite": True
        }
        
        await self.update_dashboard(dashboard_uid, update_data)
        
        # Очищаем кэш дашборда для обеспечения согласованности данных
        cache_key = f"dashboard_{dashboard_uid}"
        if cache_key in self._cache:
            del self._cache[cache_key]

    async def get_panel(self, dashboard_uid: str, panel_id: int) -> Dict:
        """Получение информации о конкретной панели"""
        dashboard = await self.get_dashboard(dashboard_uid)
        panels = dashboard["dashboard"].get("panels", [])
        
        for panel in panels:
            if panel.get("id") == panel_id:
                return panel
                
        raise GrafanaApiError(f"Panel {panel_id} not found")

    async def delete_dashboard(self, uid: str) -> None:
        """Удаление дашборда по UID"""
        try:
            await self._make_request("DELETE", f"/api/dashboards/uid/{uid}")
            cache_key = f"dashboard_{uid}"
            if cache_key in self._cache:
                del self._cache[cache_key]
        except GrafanaApiError as e:
            logging.error(f"Failed to delete dashboard {uid}: {e}")
            raise

    async def duplicate_dashboard(self, uid: str) -> Dict:
        """Дублирование дашборда"""
        dashboard = await self.get_dashboard(uid)
        dash_data = dashboard["dashboard"].copy()
        dash_data.pop("id", None)
        dash_data["title"] = f"{dash_data.get('title', '')} (Copy)"
        dash_data["uid"] = None  # Позволяет Grafana сгенерировать новый UID
        return await self.create_dashboard({"dashboard": dash_data, "overwrite": False})