from fastapi import FastAPI
from config import settings
from src.api.dashboards import router as dashboards_router
from src.api.metrics import router as metrics_router
from src.schemas.dashboard import HealthCheck
import logging



# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="Dashboards Service", version=settings.get('service_version', '1.0.0'))

# ВАЖНО: Подключаем metrics_router ПЕРЕД dashboards_router
# чтобы избежать конфликта с маршрутом /api/dashboards/{uid}
app.include_router(metrics_router, prefix="/api", tags=["metrics"])
app.include_router(dashboards_router, prefix="/api", tags=["dashboards"])

@app.get("/healthz", response_model=HealthCheck, tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.get('service_version', '1.0.0')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
