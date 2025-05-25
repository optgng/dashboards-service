#!/usr/bin/env python3
"""Специальный тест для проверки исправленных панельных операций"""

import requests
import json
import time
import socket

# Возможные базовые URL для тестирования
POSSIBLE_BASE_URLS = [
    "http://localhost:8050",
    "http://127.0.0.1:8050", 
    "http://dashboards-service.localhost:8050"
]

BASE_URL = None

def print_test_header(test_name):
    print(f"\n=== {test_name} ===")

def print_success(message):
    print(f"✅ PASS: {message}")

def print_error(message):
    print(f"❌ FAIL: {message}")

def print_info(message):
    print(f"📝 INFO: {message}")

def check_service_availability():
    """Проверяет доступность сервиса и определяет рабочий URL"""
    global BASE_URL
    
    print_info("Проверка доступности сервиса...")
    
    for url in POSSIBLE_BASE_URLS:
        try:
            print_info(f"Проверяем {url}")
            response = requests.get(f"{url}/healthz", timeout=5)
            if response.status_code == 200:
                BASE_URL = url
                print_success(f"Сервис доступен по адресу: {BASE_URL}")
                return True
        except requests.exceptions.RequestException as e:
            print_info(f"URL {url} недоступен: {str(e)}")
            continue
    
    print_error("Сервис недоступен по всем проверенным адресам!")
    print_info("Убедитесь что:")
    print_info("1. Docker контейнер dashboards-service запущен")
    print_info("2. Порт 8050 открыт")
    print_info("3. Сервис прошел health check")
    return False

def wait_for_service(max_wait_time=60):
    """Ждет пока сервис станет доступным"""
    print_info(f"Ожидание доступности сервиса (максимум {max_wait_time} секунд)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if check_service_availability():
            return True
        print_info("Ждем 5 секунд перед повторной проверкой...")
        time.sleep(5)
    
    return False

def test_panel_operations():
    """Тестирование всех операций с панелями"""
    
    # Проверяем доступность сервиса перед началом тестов
    if not check_service_availability():
        if not wait_for_service():
            print_error("Сервис недоступен. Тесты отменены.")
            return False
    
    # Переменные для тестов
    dashboard_uid = None
    panel_id = None
    
    try:
        print_test_header("1. Создание тестового дашборда")
        
        # Создание дашборда для тестирования панелей
        dashboard_data = {
            "dashboard": {
                "title": "Panel Operations Test Dashboard",
                "tags": ["test", "panels"],
                "panels": [],
                "timezone": "browser",
                "schemaVersion": 16
            },
            "folderId": 0,
            "overwrite": True
        }
        
        response = requests.post(f"{BASE_URL}/api/", json=dashboard_data, timeout=10)
        if response.status_code == 201:
            result = response.json()
            dashboard_uid = result["uid"]
            print_success(f"Dashboard created with UID: {dashboard_uid}")
        else:
            print_error(f"Failed to create dashboard: {response.status_code} - {response.text}")
            return False
        
        print_test_header("2. Создание панели")
        
        # Создание панели
        panel_data = {
            "title": "Test Panel",
            "type": "graph", 
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "targets": [{
                "refId": "A",
                "expr": "up",
                "datasource": {
                    "type": "prometheus", 
                    "uid": "prometheus"
                },
                "format": "time_series"
            }],
            "gridPos": {
                "h": 8,
                "w": 12,
                "x": 0,
                "y": 0
            },
            "options": {}
        }
        
        response = requests.post(f"{BASE_URL}/api/{dashboard_uid}/panels", json=panel_data)
        if response.status_code == 200:
            result = response.json()
            panel_id = result.get("id")
            print_success(f"Panel created with ID: {panel_id}")
        else:
            print_error(f"Failed to create panel: {response.status_code} - {response.text}")
            return False
            
        print_test_header("3. Получение панели по ID")
        
        # Получение панели
        response = requests.get(f"{BASE_URL}/api/{dashboard_uid}/panels/{panel_id}")
        if response.status_code == 200:
            result = response.json()
            print_success(f"Panel retrieved: {result.get('title', 'No title')}")
            print_info(f"Panel ID: {result.get('id')}, Type: {result.get('type')}")
        else:
            print_error(f"Failed to get panel: {response.status_code} - {response.text}")
            
        print_test_header("4. Обновление панели")
        
        # Обновление панели
        updated_panel_data = {
            "title": "Updated Test Panel",
            "type": "graph",
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus" 
            },
            "targets": [{
                "refId": "A",
                "expr": "cpu_usage",
                "datasource": {
                    "type": "prometheus",
                    "uid": "prometheus"
                },
                "format": "time_series"
            }],
            "gridPos": {
                "h": 9,
                "w": 14,
                "x": 0,
                "y": 0
            },
            "options": {"legend": {"displayMode": "table"}}
        }
        
        response = requests.put(f"{BASE_URL}/dashboards/{dashboard_uid}/panels/{panel_id}", json=updated_panel_data)
        if response.status_code == 200:
            result = response.json()
            print_success(f"Panel updated: {result.get('title', 'No title')}")
        else:
            print_error(f"Failed to update panel: {response.status_code} - {response.text}")
            
        print_test_header("5. Проверка обновленной панели")
        
        # Проверяем обновленную панель
        response = requests.get(f"{BASE_URL}/dashboards/{dashboard_uid}/panels/{panel_id}")
        if response.status_code == 200:
            result = response.json()
            if result.get("title") == "Updated Test Panel":
                print_success(f"Panel successfully updated: {result.get('title')}")
            else:
                print_error(f"Panel title not updated correctly: {result.get('title')}")
        else:
            print_error(f"Failed to verify updated panel: {response.status_code}")
            
        print_test_header("6. Удаление панели")
        
        # Удаление панели
        response = requests.delete(f"{BASE_URL}/dashboards/{dashboard_uid}/panels/{panel_id}")
        if response.status_code in [200, 204]:
            print_success("Panel deleted successfully")
        else:
            print_error(f"Failed to delete panel: {response.status_code} - {response.text}")
            
        print_test_header("7. Проверка удаления панели")
        
        # Проверяем, что панель удалена
        response = requests.get(f"{BASE_URL}/dashboards/{dashboard_uid}/panels/{panel_id}")
        if response.status_code == 404:
            print_success("Panel successfully deleted (404 Not Found)")
        else:
            print_error(f"Panel still exists after deletion: {response.status_code}")
            
        print_test_header("8. Очистка - удаление тестового дашборда")
        
        # Удаляем тестовый дашборд
        response = requests.delete(f"{BASE_URL}/api/{dashboard_uid}")
        if response.status_code in [200, 204]:
            print_success("Test dashboard deleted")
        else:
            print_error(f"Failed to delete test dashboard: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError as e:
        print_error(f"Ошибка подключения к сервису: {e}")
        print_info("Проверьте что сервис запущен и доступен")
        return False
    except requests.exceptions.Timeout as e:
        print_error(f"Таймаут запроса: {e}")
        return False
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕННЫХ ПАНЕЛЬНЫХ ОПЕРАЦИЙ")
    print("=" * 55)
    
    success = test_panel_operations()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПАНЕЛЕЙ ПРОШЛИ УСПЕШНО!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("\n💡 СОВЕТЫ ПО УСТРАНЕНИЮ ПРОБЛЕМ:")
        print("1. Запустите: docker-compose up dashboards-service")
        print("2. Проверьте: docker-compose ps")
        print("3. Проверьте логи: docker-compose logs dashboards-service")
        print("4. Убедитесь что порт 8050 свободен: netstat -an | findstr 8050")
    print("=" * 55)
