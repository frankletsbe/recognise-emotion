# PowerShell script to reset camera by restarting the Windows Camera service
# Run this as Administrator if needed

Write-Host "Camera Reset Script" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host ""

# Method 1: Kill any processes using the camera
Write-Host "Method 1: Closing applications that might be using the camera..." -ForegroundColor Yellow

$cameraProcesses = @(
    "python",
    "pythonw",
    "Teams",
    "Skype",
    "Zoom",
    "Discord",
    "obs64",
    "obs32"
)

foreach ($processName in $cameraProcesses) {
    $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "  Found $($processes.Count) $processName process(es)" -ForegroundColor Gray
        # Uncomment the line below to actually kill the processes
        # $processes | Stop-Process -Force
        # Write-Host "  Killed $processName processes" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Method 2: Restarting Windows Camera Frame Server..." -ForegroundColor Yellow

# Restart the Windows Camera Frame Server service
try {
    $service = Get-Service -Name "FrameServer" -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq "Running") {
            Write-Host "  Stopping FrameServer service..." -ForegroundColor Gray
            Stop-Service -Name "FrameServer" -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
        }
        Write-Host "  Starting FrameServer service..." -ForegroundColor Gray
        Start-Service -Name "FrameServer" -ErrorAction Stop
        Write-Host "  ✓ FrameServer service restarted successfully" -ForegroundColor Green
    } else {
        Write-Host "  FrameServer service not found (might not be needed on this system)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ✗ Could not restart FrameServer service (may need Administrator privileges)" -ForegroundColor Red
    Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Method 3: Disabling and re-enabling camera device..." -ForegroundColor Yellow
Write-Host "  (This requires Administrator privileges and pnputil)" -ForegroundColor Gray
Write-Host "  Skipping automatic execution - run manually if needed" -ForegroundColor Gray

Write-Host ""
Write-Host "Camera reset complete!" -ForegroundColor Green
Write-Host "Wait 5 seconds before trying to use the camera again." -ForegroundColor Cyan
