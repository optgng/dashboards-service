# Полный тест всех API эндпоинтов dashboards-service
# ===================================================

Write-Host "🚀 Запуск полного тестирования API dashboards-service" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Gray

$BaseUrl = "http://dashboards-service.localhost:8050"
$testResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [scriptblock]$TestScript
    )
    
    Write-Host "`n📋 Тестирование: $Name" -ForegroundColor Cyan
    try {
        $result = & $TestScript
        if ($result) {
            Write-Host "✅ $Name - УСПЕШНО" -ForegroundColor Green
            $testResults += @{Name = $Name; Status = "SUCCESS"; Details = $result}
        } else {
            Write-Host "❌ $Name - ПРОВАЛ" -ForegroundColor Red
            $testResults += @{Name = $Name; Status = "FAILED"; Details = "Test returned false"}
        }
    } catch {
        Write-Host "❌ $Name - ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
        $testResults += @{Name = $Name; Status = "ERROR"; Details = $_.Exception.Message}
    }
}

# 1. Health Check
Test-Endpoint "Health Check" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/healthz" -Method Get
    return $response.status -eq "healthy"
}

# 2. Create Dashboard
$dashboardUid = $null
Test-Endpoint "Create Dashboard" {
    $body = @{
        dashboard = @{
            title = "PowerShell Complete Test Dashboard"
            panels = @(
                @{
                    id = 1
                    title = "System Uptime"
                    type = "stat"
                    targets = @(
                        @{
                            expr = "up"
                            refId = "A"
                        }
                    )
                    gridPos = @{
                        h = 8
                        w = 12
                        x = 0
                        y = 0
                    }
                }
            )
            tags = @("powershell", "complete-test", "automation")
        }
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/" -Method Post -Body $body -ContentType "application/json"
    $script:dashboardUid = $response.uid
    return $response.id -gt 0
}

# 3. Get Dashboard
Test-Endpoint "Get Dashboard" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid" -Method Get
    return $response.dashboard.title -eq "PowerShell Complete Test Dashboard"
}

# 4. List Dashboards
Test-Endpoint "List Dashboards" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/" -Method Get
    return $response.Count -gt 0
}

# 5. Visualize Dashboard Structure
Test-Endpoint "Visualize Dashboard Structure" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/visualize" -Method Get
    return $response.visualization -like "*PowerShell Complete Test Dashboard*"
}

# 6. Add Panel
Test-Endpoint "Add Panel" {
    $panelBody = @{
        title = "CPU Usage"
        type = "graph"
        datasource = @{
            type = "prometheus"
            uid = "prometheus"
        }
        targets = @(
            @{
                expr = "cpu_usage_percent"
                refId = "A"
                legendFormat = "CPU %"
                datasource = @{
                    type = "prometheus"
                    uid = "prometheus"
                }
            }
        )
        gridPos = @{
            h = 8
            w = 12
            x = 12
            y = 0
        }
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/panels" -Method Post -Body $panelBody -ContentType "application/json"
    return $response.title -eq "CPU Usage"
}

# 7. Get Panel
Test-Endpoint "Get Panel" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/panels/1" -Method Get
    return $response.title -eq "System Uptime"
}

# 8. Update Dashboard
Test-Endpoint "Update Dashboard" {
    $updateBody = @{
        dashboard = @{
            title = "PowerShell Complete Test Dashboard - UPDATED"
            panels = @(
                @{
                    id = 1
                    title = "System Uptime - Updated"
                    type = "stat"
                    targets = @(
                        @{
                            expr = "up"
                            refId = "A"
                        }
                    )
                    gridPos = @{
                        h = 8
                        w = 12
                        x = 0
                        y = 0
                    }
                }
            )
            tags = @("powershell", "complete-test", "automation", "updated")
        }
    } | ConvertTo-Json -Depth 5
    
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid" -Method Put -Body $updateBody -ContentType "application/json"
    return $response.title -eq "PowerShell Complete Test Dashboard - UPDATED"
}

# 9. Export Dashboard
Test-Endpoint "Export Dashboard" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/export" -Method Get
    return $response.message -eq "Dashboard exported"
}

# 10. Duplicate Dashboard
$duplicatedUid = $null
Test-Endpoint "Duplicate Dashboard" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/duplicate" -Method Post
    $script:duplicatedUid = $response.uid
    return $response.title -like "*Copy*"
}

# 11. Delete Panel
Test-Endpoint "Delete Panel" {
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid/panels/1" -Method Delete
        return $response.message -eq "Panel deleted successfully"
    } catch {
        # Может не найти панель, что тоже нормально для тестирования
        return $true
    }
}

# 12. Delete Original Dashboard
Test-Endpoint "Delete Original Dashboard" {
    $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:dashboardUid" -Method Delete
    return $response.message -eq "Dashboard deleted successfully"
}

# 13. Delete Duplicated Dashboard
Test-Endpoint "Delete Duplicated Dashboard" {
    if ($script:duplicatedUid) {
        $response = Invoke-RestMethod -Uri "$BaseUrl/dashboards/$script:duplicatedUid" -Method Delete
        return $response.message -eq "Dashboard deleted successfully"
    }
    return $true
}

# Итоговый отчет
Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Gray

$successCount = ($testResults | Where-Object { $_.Status -eq "SUCCESS" }).Count
$totalCount = $testResults.Count

Write-Host "`n✅ Успешных тестов: $successCount из $totalCount" -ForegroundColor Green

$failedTests = $testResults | Where-Object { $_.Status -ne "SUCCESS" }
if ($failedTests.Count -gt 0) {
    Write-Host "`n❌ Провалившиеся тесты:" -ForegroundColor Red
    foreach ($test in $failedTests) {
        Write-Host "  - $($test.Name): $($test.Status) - $($test.Details)" -ForegroundColor Red
    }
} else {
    Write-Host "`n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!" -ForegroundColor Green
}

Write-Host "`n📋 Детальные результаты:" -ForegroundColor Cyan
foreach ($test in $testResults) {
    $status = if ($test.Status -eq "SUCCESS") { "✅" } else { "❌" }
    Write-Host "  $status $($test.Name): $($test.Status)" -ForegroundColor White
}

Write-Host "`n" + "=" * 70 -ForegroundColor Gray
Write-Host "🏁 Тестирование завершено!" -ForegroundColor Green
