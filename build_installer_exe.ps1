$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$issPath = Join-Path $projectRoot "installer\voice_assistant.iss"

if (-not (Test-Path $issPath)) {
    throw "Missing installer script: $issPath"
}

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if ($iscc) {
    $isccPath = $iscc.Source
}
else {
    $candidatePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    $isccPath = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $isccPath) {
    throw "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6, then rerun build_installer_exe.ps1"
}

Set-Location (Join-Path $projectRoot "installer")
& $isccPath "voice_assistant.iss"

$latestExe = Get-ChildItem (Join-Path $projectRoot "dist") -Filter "AI-Voice-Assistant-Installer*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($latestExe) {
    Write-Host "Installer EXE created: $($latestExe.FullName)" -ForegroundColor Green
}
