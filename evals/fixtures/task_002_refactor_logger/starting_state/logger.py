"""Logging utilities for the application.

Each function below handles its own formatting. This is messy — they should
be unified into a single log(level, message) function.
"""
import sys
from datetime import datetime


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def debug(message: str) -> None:
    """Print a DEBUG-level message to stdout."""
    print(f"[{_timestamp()}] [DEBUG] {message}")


def info(message: str) -> None:
    """Print an INFO-level message to stdout."""
    ts = _timestamp()
    print(f"[{ts}] [INFO] {message}", flush=True)


def warn(message: str) -> None:
    """Print a WARN-level message to stderr.

    Note: this one goes to stderr, unlike debug/info above.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # duplicated — should reuse _timestamp
    print(f"[{ts}] [WARN] {message}", file=sys.stderr)


def error(message: str) -> None:
    """Print an ERROR-level message to stderr and flush immediately."""
    ts = _timestamp()
    print(f"[{ts}] [ERROR] {message}", file=sys.stderr, flush=True)


def critical(message: str) -> None:
    """Print a CRITICAL-level message to stderr.

    Also prints a separator line — inconsistent with the other functions.
    """
    ts = _timestamp()
    print("=" * 60, file=sys.stderr)
    print(f"[{ts}] [CRITICAL] {message}", file=sys.stderr, flush=True)
    print("=" * 60, file=sys.stderr)
