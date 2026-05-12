#!/usr/bin/env bash
# specwarden installer for macOS / Linux / WSL.
# Usage: curl -fsSL https://raw.githubusercontent.com/<user>/specwarden/main/install.sh | bash

set -euo pipefail

OS="$(uname -s)"
case "$OS" in
    Darwin|Linux) ;;
    *)
        echo "specwarden: install.sh only supports macOS, Linux, and WSL." >&2
        echo "Detected: $OS" >&2
        echo "For Windows, use install.ps1 instead." >&2
        exit 1
        ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
    echo "specwarden: python3 is required but not found on PATH." >&2
    echo "Install Python 3.10+ first." >&2
    exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_MAJOR="${PYTHON_VERSION%.*}"
PYTHON_MINOR="${PYTHON_VERSION#*.}"
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo "specwarden: requires Python 3.10 or newer; found $PYTHON_VERSION." >&2
    exit 1
fi

if ! command -v pipx >/dev/null 2>&1; then
    echo "specwarden: pipx is required but not found." >&2
    case "$OS" in
        Darwin)
            echo "  Install with: brew install pipx" >&2
            ;;
        Linux)
            echo "  Install with: sudo apt-get install pipx (Debian/Ubuntu)" >&2
            echo "             or: python3 -m pip install --user pipx" >&2
            ;;
    esac
    exit 1
fi

echo "Installing specwarden via pipx..."
pipx install specwarden

echo
echo "specwarden installed."
echo
echo "Next steps:"
echo "  cd <your-repo>"
echo "  specwarden init                     # Wires .claude/settings.json + hooks"
echo "  specwarden git-hook install         # Installs prepare-commit-msg hook"
echo "  specwarden new <slug> --author <name>"
echo
echo "See https://github.com/<user>/specwarden for the full guide."
