param(
    [switch]$WithWhisper
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

function Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Step "Checking Python"
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "Python was not found in PATH. Install Python 3.10+ and rerun."
}

Step "Creating virtual environment"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$venvPython = Join-Path (Resolve-Path ".venv\Scripts").Path "python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment python not found at $venvPython"
}

Step "Upgrading packaging tools"
& $venvPython -m pip install --upgrade pip setuptools wheel

Step "Installing core dependencies"
& $venvPython -m pip install -r requirements.txt

Step "Installing Windows audio dependency (PyAudio)"
try {
    & $venvPython -m pip install -r requirements-windows-audio.txt
}
catch {
    Write-Warning "PyAudio wheel install failed. Trying pipwin fallback..."
    try {
        & $venvPython -m pip install pipwin
        & $venvPython -m pipwin install pyaudio
    }
    catch {
        throw "Failed to install PyAudio. Install Visual C++ Build Tools, then rerun install.ps1"
    }
}

if ($WithWhisper) {
    Step "Installing optional Whisper dependencies"
    & $venvPython -m pip install -r requirements-whisper.txt
}

Step "Preparing environment file"
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

Step "Running import health check"
& $venvPython -c "import speech_recognition, pyttsx3, dotenv, google.generativeai; print('health check ok')"

Write-Host "`nInstall completed successfully." -ForegroundColor Green
Write-Host "Run: .\\run.bat"
