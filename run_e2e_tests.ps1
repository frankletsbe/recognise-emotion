# End-to-End Test Runner for Emotion Recognition App
# This script helps run the E2E tests with proper setup

Write-Host "=== Emotion Recognition E2E Test Runner ===" -ForegroundColor Cyan
Write-Host ""

# Check if selenium is installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$seleniumInstalled = pip list | Select-String "selenium"

if (-not $seleniumInstalled) {
    Write-Host "Installing selenium..." -ForegroundColor Yellow
    pip install selenium>=4.15.0
}

# Check if Chrome is installed
$chromePath = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' -ErrorAction SilentlyContinue
if (-not $chromePath) {
    Write-Host "WARNING: Chrome not detected. E2E tests may be skipped." -ForegroundColor Red
    Write-Host "Please install Google Chrome to run browser-based tests." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Running end-to-end tests..." -ForegroundColor Green
Write-Host ""

# Run the tests
pytest tests/test_expression.py -v -s

Write-Host ""
Write-Host "=== Test run complete ===" -ForegroundColor Cyan
