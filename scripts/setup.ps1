<#
.SYNOPSIS
    One-command idempotent environment setup script for Windows (PowerShell).
.DESCRIPTION
    Creates virtual environment, installs pinned requirements, runs the test suite,
    and displays next steps.
#>
$ErrorActionPreference = "Stop"

Write-Host "=== Setting up Fractional Approval Agent (Windows) ===" -ForegroundColor Cyan

# 1. Verify Python availability
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3 is required but was not found on PATH. Please install Python 3.10+."
    exit 1
}

# 2. Create virtual environment if missing
$venvPath = Join-Path $PSScriptRoot "..\.venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[1/4] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment."
        exit 1
    }
} else {
    Write-Host "[1/4] Virtual environment already exists (.venv)." -ForegroundColor Green
}

# 3. Install pinned dependencies
$reqFile = Join-Path $PSScriptRoot "..\requirements.txt"
Write-Host "[2/4] Installing pinned dependencies from requirements.txt..." -ForegroundColor Yellow
& $venvPython -m pip install -r $reqFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies from requirements.txt."
    exit 1
}

# 4. Copy .env.example to .env if missing
$envExample = Join-Path $PSScriptRoot "..\.env.example"
$envFile = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "Copying .env.example to .env (offline mode default)..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
}

# 5. Run test suite
Write-Host "[3/4] Running pytest suite to verify installation..." -ForegroundColor Yellow
$pytestExe = Join-Path $venvPath "Scripts\pytest.exe"
& $pytestExe
if ($LASTEXITCODE -ne 0) {
    Write-Error "Test suite verification failed."
    exit 1
}

# 6. Print next steps
Write-Host "`n[4/4] Setup complete! All systems operational." -ForegroundColor Green
Write-Host "`n--- Next Steps ---" -ForegroundColor Cyan
Write-Host "1. Activate virtual environment:"
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run test suite:"
Write-Host "   pytest -v" -ForegroundColor White
Write-Host "3. Launch Streamlit Proof Viewer:"
Write-Host "   streamlit run app/streamlit_app.py" -ForegroundColor White
Write-Host "------------------" -ForegroundColor Cyan
