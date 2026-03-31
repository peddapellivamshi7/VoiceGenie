param(
    [switch]$WithWhisper
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

function Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Test-Dependencies([string]$PythonExe) {
    if (-not (Test-Path $PythonExe)) {
        return $false
    }

    $outFile = Join-Path $env:TEMP "va_depcheck_out.txt"
    $errFile = Join-Path $env:TEMP "va_depcheck_err.txt"
    Remove-Item $outFile,$errFile -ErrorAction SilentlyContinue
    try {
        & $PythonExe '-W' 'ignore::FutureWarning' '-c' 'import dotenv, speech_recognition, pyttsx3, google.generativeai' > $outFile 2> $errFile
        return $true
    }
    catch {
        return $false
    }
}

function Test-GeminiKey([string]$EnvPath) {
    if (-not (Test-Path $EnvPath)) {
        return $false
    }

    $line = Get-Content $EnvPath | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=' } | Select-Object -First 1
    if (-not $line) {
        return $false
    }

    $value = ($line -split '=', 2)[1].Trim()
    if (-not $value) {
        return $false
    }

    if ($value -match 'your_real_key_here|your_real_key') {
        return $false
    }

    return $true
}

$venvPython = Join-Path $scriptRoot ".venv\Scripts\python.exe"
$needsInstall = $false

if (-not (Test-Path $venvPython)) {
    $needsInstall = $true
}
elseif (-not (Test-Dependencies $venvPython)) {
    $needsInstall = $true
}

if ($needsInstall) {
    Step "Runtime not ready. Running installer"
    if ($WithWhisper) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$scriptRoot\install.ps1" -WithWhisper
    }
    else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$scriptRoot\install.ps1"
    }
}

$venvPython = Join-Path $scriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Runtime python not found at $venvPython"
}

if (-not (Test-Dependencies $venvPython)) {
    throw "Dependencies are still missing after installation. Open install.ps1 manually to see pip errors."
}

$envPath = Join-Path $scriptRoot ".env"
if (-not (Test-Path $envPath)) {
    Step "Creating .env from template"
    Copy-Item "$scriptRoot\.env.example" $envPath
}

if (-not (Test-GeminiKey $envPath)) {
    Write-Host "`nGEMINI_API_KEY is missing in .env" -ForegroundColor Yellow
    Write-Host "Open this file and set your key: $envPath" -ForegroundColor Yellow
    exit 1
}

Step "Starting assistant"
& $venvPython "$scriptRoot\main.py"
