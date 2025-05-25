#!/usr/bin/env python3
"""Финальный интеграционный тест всех функций dashboards-service"""

import requests
import json
import time

# Возможные базовые URL для тестирования
POSSIBLE_BASE_URLS = [
    "http://localhost:8050",
    "http://127.0.0.1:8050", 
    "http://dashboards-service.localhost:8050"
]

BASE_URL = None

def check_service_availability():
    """Проверяет доступность сервиса и определяет рабочий URL"""
    global BASE_URL
    
    print("📝 INFO: Проверка доступности сервиса...")
    
    for url in POSSIBLE_BASE_URLS:
        try:
            print(f"📝 INFO: Проверяем {url}")
            response = requests.get(f"{url}/healthz", timeout=5)
            if response.status_code == 200:
                BASE_URL = url
                print(f"✅ PASS: Сервис доступен по адресу: {BASE_URL}")
                return True
        except requests.exceptions.RequestException:
            continue
    
    print("❌ FAIL: Сервис недоступен по всем проверенным адресам!")
    return False

def test_health_check():
    """Тестирует эндпоинт проверки здоровья"""
    response = requests.get(f"{BASE_URL}/healthz")
    return response.status_code == 200

def test_list_dashboards():
    """Тестирует получение списка дашбордов"""
    response = requests.get(f"{BASE_URL}/api")
    return response.status_code == 200

def test_get_folders():
    """Тестирует получение папок"""
    response = requests.get(f"{BASE_URL}/api/folders")
    return response.status_code == 200

def test_create_dashboard():
    """Тестирует создание дашборда"""
    new_dashboard = {
        "name": "Тестовый дашборд",
        "type": "flot",
        "options": {}
    }
    response = requests.post(f"{BASE_URL}/api", json=new_dashboard)
    return response.status_code == 201

def test_get_dashboard():
    """Тестирует получение дашборда по ID"""
    dashboard_id = 1  # Замените на актуальный ID
    response = requests.get(f"{BASE_URL}/api/{dashboard_id}")
    return response.status_code == 200

def test_update_dashboard():
    """Тестирует обновление дашборда"""
    dashboard_id = 1  # Замените на актуальный ID
    updated_dashboard = {
        "name": "Обновлённый дашборд",
        "type": "graph",
        "options": {}
    }
    response = requests.put(f"{BASE_URL}/api/{dashboard_id}", json=updated_dashboard)
    return response.status_code == 200

def test_dashboard_panels():
    """Тестирует панели дашборда"""
    dashboard_id = 1  # Замените на актуальный ID
    response = requests.get(f"{BASE_URL}/api/{dashboard_id}/panels")
    return response.status_code == 200

def test_delete_dashboard():
    """Тестирует удаление дашборда"""
    dashboard_id = 1  # Замените на актуальный ID
    response = requests.delete(f"{BASE_URL}/api/{dashboard_id}")
    return response.status_code == 204

def test_data_sources():
    """Тестирует источники данных"""
    response = requests.get(f"{BASE_URL}/api/datasources")
    return response.status_code == 200

def test_prometheus_integration():
    """Тестирует интеграцию с Prometheus"""
    response = requests.get(f"{BASE_URL}/api/prometheus")
    return response.status_code == 200

def test_error_handling():
    """Тестирует обработку ошибок"""
    response = requests.get(f"{BASE_URL}/api/invalid-endpoint")
    return response.status_code == 404

def test_performance():
    """Тестирует производительность (пример: время ответа на запрос)"""
    start = time.time()
    requests.get(f"{BASE_URL}/api")
    duration = time.time() - start
    return duration < 2  # Ожидаем, что запрос выполнится быстрее 2 секунд

def test_grafana_metrics():
    """Тестирует endpoint метрик Grafana (Prometheus формат)"""
    response = requests.get(f"{BASE_URL}/api/metrics", timeout=15)
    
    if response.status_code == 200:
        metrics_text = response.text
        
        # Проверяем наличие всех обязательных метрик в Prometheus формате
        required_metrics = [
            "grafana_dashboards_total",
            "grafana_panels_total", 
            "grafana_api_response_time_milliseconds",
            "grafana_health_status"
        ]
        
        for metric in required_metrics:
            if metric not in metrics_text:
                print(f"❌ Отсутствует метрика: {metric}")
                return False
        
        print(f"📊 Prometheus метрики успешно получены")
        return True
    
    return False

def test_json_metrics():
    """Тестирует endpoint метрик в JSON формате"""
    response = requests.get(f"{BASE_URL}/api/metrics/json", timeout=15)
    
    if response.status_code == 200:
        metrics = response.json()
        
        # Проверяем наличие всех обязательных полей
        required_fields = ["total_dashboards", "total_panels", "api_response_time_ms", "grafana_health_status"]
        
        for field in required_fields:
            if field not in metrics:
                print(f"❌ Отсутствует поле: {field}")
                return False
        
        print(f"📊 Дашбордов: {metrics['total_dashboards']}")
        print(f"📈 Панелей: {metrics['total_panels']}")
        print(f"⏱️ Время ответа: {metrics['api_response_time_ms']}ms")
        print(f"💚 Grafana здорова: {metrics['grafana_health_status']}")
        
        return True
    
    return False

def test_metrics_summary():
    """Тестирует endpoint сводки метрик"""
    response = requests.get(f"{BASE_URL}/api/metrics/summary", timeout=10)
    
    if response.status_code == 200:
        summary = response.json()
        
        # Проверяем структуру ответа
        required_keys = ["summary", "details", "endpoints", "raw_metrics"]
        
        for key in required_keys:
            if key not in summary:
                print(f"❌ Отсутствует ключ в summary: {key}")
                return False
        
        print(f"📝 Summary: {summary.get('summary', 'N/A')}")
        return True
    
    return False

def run_all_tests():
    """Запускает все тесты"""
    
    # Проверяем доступность сервиса
    if not check_service_availability():
        print("❌ FAIL: Сервис недоступен. Тесты отменены.")
        print("\n💡 СОВЕТЫ ПО УСТРАНЕНИЮ ПРОБЛЕМ:")
        print("1. Запустите: docker-compose up dashboards-service")
        print("2. Проверьте: docker-compose ps") 
        print("3. Проверьте логи: docker-compose logs dashboards-service")
        print("4. Убедитесь что порт 8050 свободен")
        return False
    
    tests = [
        ("Health Check", test_health_check),
        ("Prometheus Metrics", test_grafana_metrics),
        ("JSON Metrics", test_json_metrics),
        ("Metrics Summary", test_metrics_summary),
        ("List Dashboards", test_list_dashboards),
        ("Get Folders", test_get_folders),
        ("Create Dashboard", test_create_dashboard),
        ("Get Dashboard", test_get_dashboard),
        ("Update Dashboard", test_update_dashboard),
        ("Dashboard Panels", test_dashboard_panels),
        ("Delete Dashboard", test_delete_dashboard),
        ("Data Sources", test_data_sources),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance),
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for i, (name, test_func) in enumerate(tests, 1):
        try:
            print(f"\n[{i:2d}/{total}] 🧪 Тестирование: {name}")
            
            if test_func():
                print(f"[{i:2d}/{total}] ✅ PASS {name}")
                passed += 1
            else:
                print(f"[{i:2d}/{total}] ❌ FAIL {name}")
                failed_tests.append(name)
                
        except requests.exceptions.ConnectionError:
            print(f"[{i:2d}/{total}] ❌ FAIL {name} - Ошибка подключения")
            failed_tests.append(name)
        except Exception as e:
            print(f"[{i:2d}/{total}] ❌ FAIL {name} - Exception: {str(e)}")
            failed_tests.append(name)
    
    # Итоговый отчет
    print("\n📊 Итоговый отчет:")
    print(f"Пройдено тестов: {passed}/{total}")
    
    if failed_tests:
        print("Неудачные тесты:")
        for test in failed_tests:
            print(f"- {test}")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()