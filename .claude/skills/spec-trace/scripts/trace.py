#!/usr/bin/env python3
"""Slash command shim for /trace — delegates to `spec-trace trace`."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str]) -> int:
    args = argv if argv else ["HEAD"]
    return subprocess.call(["spec-trace", "trace", *args])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
