#Requires -Version 5.1
# specwarden installer for Windows PowerShell.
# Usage:
#   irm https://raw.githubusercontent.com/<user>/specwarden/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (-not (Test-CommandExists "python")) {
    Write-Host "specwarden: python is required but not found on PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10 or newer from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

$pyVersion = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
$parts = $pyVersion -split '\.'
$major = [int]$parts[0]
$minor = [int]$parts[1]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "specwarden: requires Python 3.10 or newer; found $pyVersion." -ForegroundColor Red
    exit 1
}

if (-not (Test-CommandExists "pipx")) {
    Write-Host "specwarden: pipx is required but not found." -ForegroundColor Red
    Write-Host "  Install with: python -m pip install --user pipx" -ForegroundColor Yellow
    Write-Host "  Then:         python -m pipx ensurepath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Installing specwarden via pipx..."
pipx install specwarden

Write-Host ""
Write-Host "specwarden installed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  cd <your-repo>"
Write-Host "  specwarden init                     # Wires .claude/settings.json + hooks"
Write-Host "  specwarden git-hook install         # Installs prepare-commit-msg hook"
Write-Host "  specwarden new <slug> --author <name>"
Write-Host ""
Write-Host "See https://github.com/<user>/specwarden for the full guide."
