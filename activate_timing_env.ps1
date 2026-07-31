# PowerShell script to activate Karnak timing analysis environment

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  KARNAK TIMING ANALYSIS ENVIRONMENT" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (!(Test-Path "karnak_timing_env\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv karnak_timing_env" -ForegroundColor Yellow
    Write-Host "Then install requirements: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate the virtual environment
Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
& "karnak_timing_env\Scripts\Activate.ps1"

Write-Host ""
Write-Host "✅ Virtual environment activated!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  python extract_karnak_logs.py karnak --timing-only" -ForegroundColor White
Write-Host "  python karnak_timing_analyzer.py karnak_logs.txt --all" -ForegroundColor White
Write-Host "  python run_analysis.py" -ForegroundColor White
Write-Host ""
Write-Host "To deactivate: deactivate" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green

# Keep the environment active
Write-Host "Environment is ready for use!" -ForegroundColor Green
