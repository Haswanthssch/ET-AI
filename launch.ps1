# AURA-EPC Launch Script (PowerShell)
# Run this from the N:\ETAI directory to start both servers

param(
    [switch]$SkipBootstrap = $false,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AURA-EPC: Automated Unified Risk & Asset Intelligence" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check for .env file
$envFile = "N:\ETAI\backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host ""
    Write-Host "  Creating .env from template..." -ForegroundColor Yellow
    Copy-Item "N:\ETAI\backend\.env.example" $envFile
    Write-Host "  ACTION REQUIRED: Edit $envFile and set GROQ_API_KEY" -ForegroundColor Red
    Write-Host ""
}

# Check if data exists; run bootstrap if missing
if (-not $SkipBootstrap) {
    $dataExists = Test-Path "N:\ETAI\backend\data\master_schedule.csv" -and
                  Test-Path "N:\ETAI\backend\data\supply_chain.csv" -and
                  Test-Path "N:\ETAI\backend\data\rfi_logs.json" -and
                  Test-Path "N:\ETAI\backend\data\spec_chunks.json"

    if (-not $dataExists) {
        Write-Host "  [1/3] Running bootstrap (data generation + model training + index build)..." -ForegroundColor Green
        Push-Location N:\ETAI\backend
        python bootstrap.py
        Pop-Location
    } else {
        Write-Host "  Data files already exist. Skipping bootstrap. (Use -SkipBootstrap to force)" -ForegroundColor Gray
    }
}

# Start FastAPI Backend
Write-Host ""
Write-Host "  [1/2] Starting FastAPI Backend on http://localhost:$BackendPort..." -ForegroundColor Green
$backendCmd = "cd N:\ETAI\backend && python -m uvicorn main:app --host 0.0.0.0 --port $BackendPort --reload"
$backendJob = Start-Process cmd -ArgumentList "/c $backendCmd" -NoNewWindow -PassThru

Start-Sleep -Seconds 5

# Start Next.js Frontend
Write-Host "  [2/2] Starting Next.js Frontend on http://localhost:$FrontendPort..." -ForegroundColor Green
$frontendCmd = "cd N:\ETAI\frontend && set NODE_OPTIONS=--max-old-space-size=4096 && npm run dev -- --port $FrontendPort"
$frontendJob = Start-Process cmd -ArgumentList "/c $frontendCmd" -NoNewWindow -PassThru

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AURA-EPC is starting up..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend API : http://localhost:$BackendPort" -ForegroundColor White
Write-Host "  API Docs    : http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host "  Frontend    : http://localhost:$FrontendPort" -ForegroundColor White
Write-Host ""
Write-Host "  Role Views:" -ForegroundColor Yellow
Write-Host "    Executive  : http://localhost:$FrontendPort/executive" -ForegroundColor White
Write-Host "    Procurement: http://localhost:$FrontendPort/procurement" -ForegroundColor White
Write-Host "    Engineer   : http://localhost:$FrontendPort/engineer" -ForegroundColor White
Write-Host "    QA/QC      : http://localhost:$FrontendPort/qa-qc" -ForegroundColor White
Write-Host ""
Write-Host "  Press Ctrl+C to stop all servers." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Keep alive
try {
    while ($true) {
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "  Stopping servers..." -ForegroundColor Yellow
    $backendJob | Stop-Process -Force -ErrorAction SilentlyContinue
    $frontendJob | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Servers stopped." -ForegroundColor Yellow
}
