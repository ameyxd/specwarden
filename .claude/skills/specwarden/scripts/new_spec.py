#!/usr/bin/env python3
"""Slash command shim for /spec — delegates to `specwarden new`."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: /spec <slug>", file=sys.stderr)
        return 2
    title = " ".join(argv)
    return subprocess.call(["specwarden", "new", title, "--author", "claude"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
