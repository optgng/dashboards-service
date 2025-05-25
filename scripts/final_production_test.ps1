# Финальный тест готовности к продакшн использованию
Write-Host "🚀 Запуск финального теста готовности к продакшн" -ForegroundColor Green

$baseUrl = "http://dashboards-service.localhost:8050"
$testPassed = 0
$testTotal = 0

# Функция для логирования результатов
function Test-Result {
    param(
        [string]$TestName,
        [bool]$Success,
        [string]$Details = ""
    )
    
    $global:testTotal++
    if ($Success) {
        $global:testPassed++
        Write-Host "✅ PASS $TestName" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL $TestName" -ForegroundColor Red
    }
    
    if ($Details) {
        Write-Host "    📝 $Details" -ForegroundColor Gray
    }
}

# Тест 1: Health Check
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/healthz" -Method Get -TimeoutSec 5
    $success = $healthResponse.status -eq "healthy"
    Test-Result "Health Check" $success "Status: $($healthResponse.status), Version: $($healthResponse.version)"
} catch {
    Test-Result "Health Check" $false "Exception: $($_.Exception.Message)"
}

# Тест 2: Список дашбордов
try {
    $dashboards = Invoke-RestMethod -Uri "$baseUrl/dashboards/" -Method Get -TimeoutSec 10
    $count = $dashboards.Count
    Test-Result "Dashboard List" $true "Found $count dashboards"
} catch {
    Test-Result "Dashboard List" $false "Exception: $($_.Exception.Message)"
}

# Тест 3: Создание дашборда
$dashboardData = @{
    dashboard = @{
        title = "Production Test Dashboard"
        timezone = "browser"
        schemaVersion = 16
        tags = @("production", "test")
        panels = @()
    }
    folderId = 0
    overwrite = $true
} | ConvertTo-Json -Depth 10

try {
    $createResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/" -Method Post -Body $dashboardData -ContentType "application/json" -TimeoutSec 10
    $dashboardUid = $createResponse.uid
    Test-Result "Dashboard Create" $true "Created dashboard with UID: $dashboardUid"
    
    # Тест 4: Чтение дашборда
    try {
        $readResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/$dashboardUid" -Method Get -TimeoutSec 5
        $title = $readResponse.dashboard.title
        Test-Result "Dashboard Read" $true "Title: $title"
    } catch {
        Test-Result "Dashboard Read" $false "Exception: $($_.Exception.Message)"
    }
    
    # Тест 5: Продвинутые функции
    try {
        $visualizeResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/$dashboardUid/visualize" -Method Get -TimeoutSec 5
        Test-Result "Dashboard Visualization" $true "Visualization successful"
    } catch {
        Test-Result "Dashboard Visualization" $false "Exception: $($_.Exception.Message)"
    }
    
    try {
        $exportResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/$dashboardUid/export" -Method Get -TimeoutSec 5
        Test-Result "Dashboard Export" $true "Export successful"
    } catch {
        Test-Result "Dashboard Export" $false "Exception: $($_.Exception.Message)"
    }
    
    # Очистка
    try {
        $deleteResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/$dashboardUid" -Method Delete -TimeoutSec 5
        Write-Host "✅ Cleanup: Dashboard deleted successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Cleanup warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
} catch {
    Test-Result "Dashboard Create" $false "Exception: $($_.Exception.Message)"
}

# Тест 6: Обработка ошибок
try {
    $errorResponse = Invoke-RestMethod -Uri "$baseUrl/dashboards/non-existent-uid" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Test-Result "Error Handling (404)" $false "Expected 404 but got success"
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Test-Result "Error Handling (404)" $true "Correctly returned 404"
    } else {
        Test-Result "Error Handling (404)" $false "Wrong status code: $($_.Exception.Response.StatusCode)"
    }
}

# Итоговый отчет
Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
Write-Host "📊 ИТОГОВЫЙ ОТЧЕТ ГОТОВНОСТИ К ПРОДАКШН" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "Пройдено тестов: $testPassed/$testTotal" -ForegroundColor White
$successRate = [math]::Round(($testPassed / $testTotal) * 100, 1)
Write-Host "Процент успеха: $successRate%" -ForegroundColor White

if ($testPassed -eq $testTotal) {
    Write-Host "`n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Сервис готов к продакшн использованию." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  ЕСТЬ ПРОБЛЕМЫ! Необходимо исправить ошибки перед продакшн развертыванием." -ForegroundColor Yellow
    exit 1
}
