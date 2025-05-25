from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Optional

class Panel(BaseModel):
    id: int
    title: str
    type: str
    datasource: Dict[str, Any]
    targets: List[Dict[str, Any]]

class DashboardMetadata(BaseModel):
    uid: str
    title: str
    description: Optional[str] = None
    tags: List[str] = []

class DashboardCreate(BaseModel):
    dashboard: Dict[str, Any]
    folderId: int = 0
    overwrite: bool = True
    message: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_dashboard(cls, values):
        if not values.dashboard.get("title"):
            raise ValueError("Field 'title' is required in the dashboard data.")
        return values

    class Config:
        json_schema_extra = {
            "example": {
                "dashboard": {
                    "title": "New Dashboard",
                    "panels": [],
                    "timezone": "browser",
                    "schemaVersion": 16
                },
                "folderId": 0,
                "overwrite": True
            }
        }

class DashboardResponse(BaseModel):
    id: int
    uid: str
    title: str
    url: str
    version: int = 1
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "uid": "test-uid",
                "title": "Test Dashboard",
                "url": "/d/test-uid/test-dashboard",
                "version": 1
            }
        }

class HealthCheck(BaseModel):
    status: str
    version: str

class PanelTarget(BaseModel):
    refId: str
    expr: str
    datasource: Dict[str, Any]
    format: str = "time_series"

class PanelCreate(BaseModel):
    title: str
    type: str = "graph"
    datasource: Dict[str, Any]
    targets: List[PanelTarget]
    gridPos: Dict[str, int] = {"h": 8, "w": 12, "x": 0, "y": 0}
    options: Dict[str, Any] = {}

class PanelUpdate(PanelCreate):
    id: Optional[int] = None

class PanelResponse(PanelUpdate):
    dashboardUid: str
    id: int  # В ответе ID всегда должен быть
