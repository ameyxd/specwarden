#Requires -Version 5.1
# spec-trace installer for Windows PowerShell.
# Usage:
#   irm https://raw.githubusercontent.com/<user>/spec-trace/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "python")) {
    Write-Host "spec-trace: python is required but not found on PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10 or newer from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

$pyVersion = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
$parts = $pyVersion -split '\.'
$major = [int]$parts[0]
$minor = [int]$parts[1]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "spec-trace: requires Python 3.10 or newer; found $pyVersion." -ForegroundColor Red
    exit 1
}

if (-not (Test-CommandExists "pipx")) {
    Write-Host "spec-trace: pipx is required but not found." -ForegroundColor Red
    Write-Host "  Install with: python -m pip install --user pipx" -ForegroundColor Yellow
    Write-Host "  Then:         python -m pipx ensurepath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing spec-trace via pipx..."
pipx install spec-trace

Write-Host ""
Write-Host "spec-trace installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  cd <your-repo>"
Write-Host "  spec-trace init                     # Wires .claude/settings.json + hooks"
Write-Host "  spec-trace git-hook install         # Installs prepare-commit-msg hook"
Write-Host "  spec-trace new <slug> --author <name>"
Write-Host ""
Write-Host "See https://github.com/<user>/spec-trace for the full guide."
