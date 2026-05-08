#!/usr/bin/env python3
"""Slash command shim for /coverage — delegates to `spec-trace coverage`."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str]) -> int:
    return subprocess.call(["spec-trace", "coverage", *argv])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
