# 🚀 Инструкции по развертыванию

## Быстрое развертывание

### 1. Подготовка окружения

```powershell
# Клонирование репозитория (если применимо)
git clone <repository-url>
cd dashboards-service

# Создание виртуального окружения
python -m venv venv
.\venv\Scripts\Activate.ps1

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Отредактируйте файл `settings.toml`:

```toml
[default]
grafana_url = "http://your-grafana-url:3000"
grafana_api_key = "your_grafana_api_key"
service_version = "1.0.0"

[development]
grafana_url = "http://localhost:3000"
grafana_api_key = "your_development_api_key"
```

### 3. Запуск сервиса

```powershell
# Разработка
python main.py

# Продакшн с Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8050

# Docker
docker build -t dashboards-service .
docker run -p 8050:8050 dashboards-service
```

### 4. Проверка готовности

```powershell
# Быстрая проверка
curl http://localhost:8050/healthz

# Полное тестирование
python tests\final_comprehensive_production_test.py
```

## Продакшн развертывание

### Docker

```dockerfile
# Используйте готовый Dockerfile
docker build -t dashboards-service:1.0.0 .
docker run -d -p 8050:8050 --name dashboards-service dashboards-service:1.0.0
```

### Systemd (Linux)

```ini
[Unit]
Description=FastAPI Dashboards Service
After=network.target

[Service]
Type=simple
User=dashboards
WorkingDirectory=/opt/dashboards-service
ExecStart=/opt/dashboards-service/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8050
Restart=always

[Install]
WantedBy=multi-user.target
```

### Windows Service

```powershell
# Установка как Windows Service (требует NSSM)
nssm install DashboardsService "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"
nssm set DashboardsService DisplayName "FastAPI Dashboards Service"
nssm start DashboardsService
```

## Мониторинг и логи

### Health Check

```shell
GET /healthz
```

### Логирование

Логи записываются в stdout. Для продакшн используйте:

- **Docker:** docker logs
- **Systemd:** journalctl -u dashboards-service
- **Windows:** Event Viewer

### Метрики

Сервис готов к интеграции с:

- Prometheus (добавьте prometheus-client)
- Grafana (для мониторинга самого сервиса)
- Health check endpoints

## 🔧 Конфигурация

### Переменные окружения

```env
SYSTEM_MONITORING_GRAFANA_URL=http://grafana:3000
SYSTEM_MONITORING_GRAFANA_API_KEY=your_api_key
SYSTEM_MONITORING_SERVICE_VERSION=1.0.0
```

### API Documentation

После запуска доступна по адресу:

- **Swagger UI:** <http://localhost:8050/docs>
- **ReDoc:** <http://localhost:8050/redoc>

## 🎯 Заключение

Сервис полностью готов к продакшн развертыванию с 100% функциональностью.

---
*Создано: 25 мая 2025 г.*
