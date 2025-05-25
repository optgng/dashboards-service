#!/usr/bin/env python3
"""
Быстрый тест готовности к продакшн - основные функции
Проверяет критически важные эндпоинты для продакшн готовности
"""

import requests
import json

BASE_URL = "http://localhost:8050"

# Глобальные переменные для тестов
created_dashboard_uid = None

def print_test_header(message):
    print(f"🚀 {message}")
    print("=" * 60)

def print_success(message):
    print(f"✅ PASS {message}")

def print_error(message):
    print(f"❌ FAIL {message}")

def print_info(message):
    print(f"    📝 {message}")

def test_health_check():
    """Тест health check эндпоинта"""
    print("1. Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        if response.status_code == 200:
            data = response.json()
            print_success("Health Check")
            print_info(f"Status: {response.status_code}, Response: {data}")
            return True
        else:
            print_error(f"Health Check - Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health Check - Error: {str(e)}")
        return False

def test_metrics_endpoints():
    """Тест новых эндпоинтов метрик"""
    print("4. Metrics Endpoints...")
    try:
        # Тест Prometheus метрик
        response = requests.get(f"{BASE_URL}/api/metrics")
        if response.status_code == 200 and "grafana_dashboards_total" in response.text:
            print_success("Prometheus Metrics")
            print_info("Prometheus format detected")
        else:
            print_error(f"Prometheus Metrics failed: {response.status_code}")
            return False
        
        # Тест JSON метрик
        response = requests.get(f"{BASE_URL}/api/metrics/json")
        if response.status_code == 200:
            data = response.json()
            print_success("JSON Metrics")
            print_info(f"Dashboards: {data.get('total_dashboards', 'N/A')}, Panels: {data.get('total_panels', 'N/A')}")
        else:
            print_error(f"JSON Metrics failed: {response.status_code}")
            return False
            
        # Тест Summary метрик
        response = requests.get(f"{BASE_URL}/api/metrics/summary")
        if response.status_code == 200:
            print_success("Metrics Summary")
            return True
        else:
            print_error(f"Metrics Summary failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Metrics Error: {str(e)}")
        return False

def test_basic_crud():
    """Тест основных CRUD операций"""
    global created_dashboard_uid
    print("2. Basic CRUD Operations...")
    
    # CREATE
    dashboard_data = {
        "dashboard": {
            "title": "Quick Test Dashboard",
            "tags": ["test"],
            "panels": [],
            "time": {"from": "now-6h", "to": "now"},
            "refresh": "30s",
            "timezone": "browser",
            "schemaVersion": 16
        },
        "folderId": 0,
        "overwrite": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/", json=dashboard_data)
        if response.status_code == 201:
            created_dashboard_uid = response.json().get("uid")
            print_success("Dashboard Create (201)")
            print_info(f"UID: {created_dashboard_uid}")
        else:
            print_error(f"Create failed: {response.status_code}")
            return False
        
        # READ
        response = requests.get(f"{BASE_URL}/api/{created_dashboard_uid}")
        if response.status_code == 200:
            print_success("Dashboard Read (200)")
        else:
            print_error(f"Read failed: {response.status_code}")
            return False
        
        # DELETE
        response = requests.delete(f"{BASE_URL}/api/{created_dashboard_uid}")
        if response.status_code in [200, 204]:
            print_success("Dashboard Delete")
            print_info("CRUD operations completed successfully")
            return True
        else:
            print_error(f"Delete failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"CRUD Error: {str(e)}")
        return False

def test_list_dashboards():
    """Тест получения списка дашбордов"""
    print("3. List Dashboards...")
    try:
        response = requests.get(f"{BASE_URL}/api/")
        if response.status_code == 200:
            dashboards = response.json()
            print_success("Dashboard List")
            print_info(f"Found {len(dashboards)} dashboards")
            return True
        else:
            print_error(f"List failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List Error: {str(e)}")
        return False

def print_final_report(results):
    """Выводит финальный отчет"""
    print("=" * 60)
    print("📊 БЫСТРЫЙ ТЕСТ ПРОДАКШН ГОТОВНОСТИ")
    print("=" * 60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"Пройдено тестов: {passed}/{total}")
    print(f"Процент успеха: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 ВСЕ ОСНОВНЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Сервис готов к продакшн использованию.")
    else:
        print("⚠️  Некоторые базовые тесты не прошли.")
        print("❌ Требуется исправление перед продакшн.")

def main():
    print_test_header("Быстрый тест готовности к продакшн")
    
    # Выполняем основные тесты
    results = [
        test_health_check(),
        test_basic_crud(),
        test_list_dashboards(),
        test_metrics_endpoints()
    ]
    
    # Финальный отчет
    print_final_report(results)
    print("🏁 Быстрый тест завершен")

if __name__ == "__main__":
    main()
