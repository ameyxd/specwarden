#!/usr/bin/env python3
"""Slash command shim for activating a spec — delegates to `specwarden activate`."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: activate_spec <spec-id>", file=sys.stderr)
        return 2
    return subprocess.call(["specwarden", "activate", argv[0]])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
