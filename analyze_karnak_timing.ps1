# Karnak Timing Analysis - PowerShell Script
# This script automates the complete workflow for Windows PowerShell users

param(
    [string]$ContainerName = "karnak",
    [string]$OutputDir = "timing_analysis",
    [switch]$Follow,
    [int]$Lines = 0
)

Write-Host "KARNAK TIMING ANALYSIS - POWERSHELL" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python and add it to PATH." -ForegroundColor Red
    exit 1
}

# Check if Docker is available
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if container is running
Write-Host "`nChecking if Karnak container is running..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>&1
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($containerStatus)) {
    Write-Host "ERROR: Karnak container '$ContainerName' is not running!" -ForegroundColor Red
    Write-Host "Please start it with: docker-compose -f docker-compose-timing.yml up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host "Container '$ContainerName' is running" -ForegroundColor Green

# Create output directory
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir" -ForegroundColor Green
}

# Generate timestamp for unique filenames
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $OutputDir "karnak_timing_logs_$timestamp.txt"

Write-Host "`nExtracting timing logs..." -ForegroundColor Yellow
Write-Host "Output file: $logFile" -ForegroundColor Cyan

if ($Follow) {
    Write-Host "Following logs in real-time (Press Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host "Logs will be saved to: $logFile" -ForegroundColor Cyan
    
    # Follow logs and save to file
    docker logs -f $ContainerName | ForEach-Object {
        if ($_ -match "TIMING") {
            Add-Content -Path $logFile -Value $_
            Write-Host $_ -ForegroundColor White
        }
    }
} else {
    # Extract logs based on parameters
    $dockerCmd = "docker logs"
    if ($Lines -gt 0) {
        $dockerCmd += " --tail $Lines"
    }
    $dockerCmd += " $ContainerName"
    
    Write-Host "Running: $dockerCmd" -ForegroundColor Cyan
    
    try {
        $logs = Invoke-Expression $dockerCmd 2>&1
        $timingLogs = $logs | Where-Object { $_ -match "TIMING" }
        
        if ($timingLogs.Count -eq 0) {
            Write-Host "WARNING: No timing data found in logs!" -ForegroundColor Yellow
            Write-Host "Make sure DICOM files are being processed through Karnak" -ForegroundColor Yellow
        } else {
            $timingLogs | Out-File -FilePath $logFile -Encoding UTF8
            Write-Host "Extracted $($timingLogs.Count) timing log entries" -ForegroundColor Green
        }
    } catch {
        Write-Host "ERROR: Failed to extract logs: $_" -ForegroundColor Red
        exit 1
    }
}

# Check if we have timing data
if (!(Test-Path $logFile) -or (Get-Item $logFile).Length -eq 0) {
    Write-Host "ERROR: No timing data found!" -ForegroundColor Red
    exit 1
}

# Install Python dependencies if needed
Write-Host "`nChecking Python dependencies..." -ForegroundColor Yellow
try {
    python -c "import matplotlib, pandas, numpy" 2>$null
    Write-Host "Dependencies are installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Run timing analysis
Write-Host "`nRunning timing analysis..." -ForegroundColor Yellow
$analysisCmd = "python karnak_timing_analyzer.py `"$logFile`" --all --output-dir `"$OutputDir`""
Write-Host "Command: $analysisCmd" -ForegroundColor Cyan

try {
    Invoke-Expression $analysisCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nAnalysis completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Analysis failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Failed to run analysis: $_" -ForegroundColor Red
    exit 1
}

# Show results
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "RESULTS" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Log file: $(Resolve-Path $logFile)" -ForegroundColor Cyan
Write-Host "Analysis directory: $(Resolve-Path $OutputDir)" -ForegroundColor Cyan

# List generated files
if (Test-Path $OutputDir) {
    Write-Host "`nGenerated files:" -ForegroundColor Yellow
    Get-ChildItem $OutputDir | ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  $($_.Name) ($size KB)" -ForegroundColor White
    }
}

Write-Host "`nTo view graphs, open the files in: $(Resolve-Path $OutputDir)" -ForegroundColor Cyan
Write-Host "To run analysis again:" -ForegroundColor Yellow
Write-Host "  python karnak_timing_analyzer.py `"$logFile`" --all" -ForegroundColor White

Write-Host "`nAnalysis complete!" -ForegroundColor Green
