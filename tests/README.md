# 🧪 Тестовые файлы

## Описание тестов

### final_test.py

Комплексный тест всех эндпоинтов включая новые метрики API.

**Запуск:**

```powershell
python tests\final_test.py
```

**Новые тесты:**

- Prometheus метрики (`/api/metrics`)
- JSON метрики (`/api/metrics/json`)
- Сводка метрик (`/api/metrics/summary`)

### quick_test.py

Быстрый тест основных функций включая метрики.

**Запуск:**

```powershell
python tests\quick_test.py
```

**Проверяет:**

- Health Check
- Prometheus метрики
- JSON метрики  
- Сводку метрик
- Список дашбордов

### panel_operations_test.py

Специализированный тест панельных операций с обновленными API URL.

**Запуск:**

```powershell
python tests\panel_operations_test.py
```

**Функции:**

- Создание панели (`/api/dashboards/{uid}/panels`)
- Получение панели
- Обновление панели  
- Удаление панели

### quick_production_test.py

Быстрый тест готовности к продакшн с метриками.

**Запуск:**

```powershell
python tests\quick_production_test.py
```

**Включает:**

- Основные CRUD операции
- Все эндпоинты метрик
- Проверку производительности

## 📊 Новые метрики API

Все тесты обновлены для работы с новыми эндпоинтами:

- `GET /api/metrics` - Prometheus формат
- `GET /api/metrics/json` - JSON формат  
- `GET /api/metrics/summary` - Удобочитаемая сводка

## 📋 Статус тестов

Все тестовые файлы обновлены и готовы для проверки сервиса с новыми метриками.
