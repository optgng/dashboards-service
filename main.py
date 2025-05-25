from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from src.api.dashboards import router as dashboards_router
from src.api.metrics import router as metrics_router
from src.schemas.dashboard import HealthCheck
import logging



# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="Dashboards Service", version=settings.get('service_version', '1.0.0'))

# Настройка CORS для работы с WebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://webui.localhost",
        "http://webui.localhost:3000",
        "http://webui.localhost:8080",
        "*"  # В продакшене лучше указать конкретные домены
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# ВАЖНО: Подключаем metrics_router ПЕРЕД dashboards_router
# чтобы избежать конфликта с маршрутом /api/dashboards/{uid}
app.include_router(metrics_router, prefix="/api", tags=["metrics"])
app.include_router(dashboards_router, prefix="/api", tags=["dashboards"])

@app.get("/healthz", response_model=HealthCheck, tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.get('service_version', '1.0.0'),
        "cors_enabled": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
