#!/usr/bin/env pwsh
# HIAI Installer for Windows (PowerShell)

$ErrorActionPreference = "Stop"

$HIAI_DIR = "$env:USERPROFILE\.local\share\hiai"
$VENV_DIR = "$HIAI_DIR\venv"
$BIN_DIR = "$env:USERPROFILE\.local\bin"
$REPO_URL = "https://github.com/toewaioo/hiai.git"

function Write-Info($msg)  { Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Fail($msg)  { Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }

function Find-Python {
    foreach ($cmd in @("python3.12", "python3.11", "python3.10", "python")) {
        try {
            $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            $major = & $cmd -c "import sys; print(sys.version_info.major)" 2>$null
            $minor = & $cmd -c "import sys; print(sys.version_info.minor)" 2>$null
            if ([int]$major -ge 3 -and [int]$minor -ge 10) {
                Write-Info "Found Python $ver at $(Get-Command $cmd | Select-Object -ExpandProperty Source)"
                return $cmd
            }
        } catch { }
    }
    Write-Fail "Python 3.10+ is required but not found."
}

Write-Host ""
Write-Host "  ╦ ╦╦╔═╗╦" -ForegroundColor Cyan
Write-Host "  ╠═╣║╠═╝║" -ForegroundColor Cyan
Write-Host "  ╩ ╩╩╩  ╩" -ForegroundColor Cyan
Write-Host ""
Write-Host "  HIAI Installer"
Write-Host "  ──────────────"
Write-Host ""

$python = Find-Python

# Clone or update
if (Test-Path "$HIAI_DIR\repo") {
    Write-Info "Updating existing installation..."
    Set-Location "$HIAI_DIR\repo"
    git pull -q
} else {
    Write-Info "Cloning HIAI repository..."
    git clone --depth 1 $REPO_URL "$HIAI_DIR\repo"
}

# Create venv
Write-Info "Creating virtual environment..."
& $python -m venv $VENV_DIR

# Install
Write-Info "Installing HIAI..."
& "$VENV_DIR\Scripts\pip.exe" install --upgrade pip -q
& "$VENV_DIR\Scripts\pip.exe" install -e "$HIAI_DIR\repo" -q

# Create wrapper script
if (-not (Test-Path $BIN_DIR)) {
    New-Item -ItemType Directory -Path $BIN_DIR -Force | Out-Null
}

$wrapper = @"
@echo off
"$VENV_DIR\Scripts\python.exe" -m hiai %*
"@
Set-Content -Path "$BIN_DIR\hiai.bat" -Value $wrapper
Write-Info "Created wrapper at $BIN_DIR\hiai.bat"

# Check PATH
$pathDirs = $env:PATH -split ";"
if ($pathDirs -notcontains $BIN_DIR) {
    Write-Warn "$BIN_DIR is not in your PATH."
    Write-Host "  Add it to your PATH:"
    Write-Host ""
    Write-Host "    [Environment]::SetEnvironmentVariable('PATH', `$env:PATH + ';$BIN_DIR', 'User')"
    Write-Host ""
} else {
    Write-Info "$BIN_DIR is already in your PATH."
}

Write-Host ""
Write-Info "Installation complete!"
Write-Host ""
Write-Host "  Run 'hiai --help' to get started."
Write-Host "  Run 'hiai config set-key' to set your OpenRouter API key."
Write-Host ""
