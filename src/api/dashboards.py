from fastapi import APIRouter, HTTPException, Path, Query, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Any, Dict, List

from src.schemas.dashboard import (
    DashboardCreate,
    DashboardResponse,
    DashboardMetadata,
    PanelCreate,
    PanelUpdate,
    PanelResponse
)
from src.services.grafana_service import GrafanaService

router = APIRouter()
grafana_service = GrafanaService()

@router.post("/", response_model=DashboardResponse, status_code=201)
async def create_dashboard(dashboard: DashboardCreate):
    try:
        return await grafana_service.create_dashboard(dashboard.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DashboardMetadata])
async def list_dashboards(
    tag: str = Query(None, description="Filter dashboards by tag"),
    search: str = Query(None, description="Search dashboards by title")
):
    try:
        return await grafana_service.get_dashboards(tag=tag, search=search)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{uid}", response_model=Dict[str, Any])
async def get_dashboard(
    uid: str = Path(..., description="Dashboard UID")
):
    try:
        return await grafana_service.get_dashboard(uid)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{uid}", response_model=DashboardResponse)
async def update_dashboard(
    uid: str,
    dashboard: DashboardCreate
):
    try:
        return await grafana_service.update_dashboard(uid, dashboard.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{uid}")
async def delete_dashboard(uid: str):
    try:
        await grafana_service.delete_dashboard(uid)
        return {"message": "Dashboard deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{uid}/duplicate", response_model=DashboardResponse)
async def duplicate_dashboard(uid: str):
    """Дублирование дашборда"""
    try:
        return await grafana_service.duplicate_dashboard(uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/import")
async def import_dashboard_from_file(file: UploadFile):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        result = await grafana_service.import_dashboard(temp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{uid}/export")
async def export_dashboard_to_file(uid: str):
    try:
        filepath = await grafana_service.export_dashboard(uid)
        return {"message": "Dashboard exported", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{uid}/compare")
async def compare_dashboard_versions(
    uid: str,
    version1: int = Query(..., description="First version to compare"),
    version2: int = Query(..., description="Second version to compare")
):
    try:
        return await grafana_service.compare_versions(uid, version1, version2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{uid}/visualize")
async def visualize_dashboard_structure(uid: str):
    try:
        dashboard = await grafana_service.get_dashboard(uid)
        return {"visualization": grafana_service.visualize_dashboard(dashboard)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Панели
@router.post("/{uid}/panels", response_model=PanelResponse)
async def create_panel(
    uid: str,
    panel: PanelCreate
):
    """Добавление новой панели на дашборд"""
    try:
        result = await grafana_service.add_panel(uid, panel.model_dump())
        return {**panel.model_dump(), "dashboardUid": uid, "id": result["panel_id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{uid}/panels/{panel_id}", response_model=PanelResponse)
async def update_panel(
    uid: str,
    panel_id: int,
    panel: PanelUpdate
):
    """Обновление существующей панели"""
    try:
        result = await grafana_service.update_panel(uid, panel_id, panel.model_dump())
        return {**panel.model_dump(), "dashboardUid": uid, "id": panel_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{uid}/panels/{panel_id}")
async def delete_panel(
    uid: str,
    panel_id: int
):
    """Удаление панели с дашборда"""
    try:
        await grafana_service.delete_panel(uid, panel_id)
        return {"message": "Panel deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{uid}/panels/{panel_id}", response_model=PanelResponse)
async def get_panel(
    uid: str,
    panel_id: int
):
    """Получение информации о конкретной панели"""
    try:
        panel = await grafana_service.get_panel(uid, panel_id)
        return {**panel, "dashboardUid": uid}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))