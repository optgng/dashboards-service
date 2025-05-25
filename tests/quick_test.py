#!/usr/bin/env python3
"""Быстрый тест основных функций dashboards-service"""

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

def quick_test():
    """Быстрая проверка основных функций"""
    
    # Проверяем доступность сервиса
    if not check_service_availability():
        print("❌ FAIL: Сервис недоступен. Тесты отменены.")
        return False
    
    tests = [
        ("Health Check", lambda: requests.get(f"{BASE_URL}/healthz", timeout=10)),
        ("Prometheus Metrics", lambda: requests.get(f"{BASE_URL}/api/metrics", timeout=10)),
        ("JSON Metrics", lambda: requests.get(f"{BASE_URL}/api/metrics/json", timeout=10)),
        ("Metrics Summary", lambda: requests.get(f"{BASE_URL}/api/metrics/summary", timeout=10)),
        ("List Dashboards", lambda: requests.get(f"{BASE_URL}/api/", timeout=10)),
    ]
    
    passed = 0
    total = len(tests)
    
    for i, (name, test_func) in enumerate(tests, 1):
        try:
            response = test_func()
            if response.status_code in [200, 201]:
                print(f"[{i:2d}/{total}] ✅ PASS {name}")
                passed += 1
                
                # Дополнительная информация для метрик
                if "Metrics" in name and response.status_code == 200:
                    if name == "JSON Metrics":
                        try:
                            data = response.json()
                            print(f"         📊 Дашбордов: {data.get('total_dashboards', 'N/A')}")
                            print(f"         📈 Панелей: {data.get('total_panels', 'N/A')}")
                            print(f"         ⏱️ Время ответа: {data.get('api_response_time_ms', 'N/A')}ms")
                        except:
                            pass
            else:
                print(f"[{i:2d}/{total}] ❌ FAIL {name}")
                print(f"         📝 Status: {response.status_code}, Response: {response.text[:100]}")
        except requests.exceptions.ConnectionError:
            print(f"[{i:2d}/{total}] ❌ FAIL {name}")
            print(f"         📝 Exception: Не удается подключиться к сервису")
        except Exception as e:
            print(f"[{i:2d}/{total}] ❌ FAIL {name}")
            print(f"         📝 Exception: {str(e)}")
    
    print(f"\n📊 Результат: {passed}/{total} тестов прошли успешно")
    return passed == total

if __name__ == "__main__":
    print("🚀 БЫСТРЫЙ ТЕСТ DASHBOARDS-SERVICE")
    print("=" * 40)
    
    success = quick_test()
    
    if not success:
        print("\n💡 СОВЕТЫ ПО УСТРАНЕНИЮ ПРОБЛЕМ:")
        print("1. Запустите: docker-compose up dashboards-service")
        print("2. Проверьте: docker-compose ps")
        print("3. Проверьте логи: docker-compose logs dashboards-service")