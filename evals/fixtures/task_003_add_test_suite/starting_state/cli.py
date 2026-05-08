"""JSON CLI — parse and format subcommands.

Usage:
    python cli.py parse <file>     Print each top-level key and its type.
    python cli.py format <file>    Pretty-print the JSON with 2-space indent.
"""
import argparse
import json
import sys
from pathlib import Path


def cmd_parse(path: str) -> int:
    """Print the top-level keys and value types from a JSON file."""
    p = Path(path)
    if not p.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print(f"error: expected a JSON object, got {type(data).__name__}", file=sys.stderr)
        return 1

    for key, value in data.items():
        print(f"{key}: {type(value).__name__}")

    return 0


def cmd_format(path: str) -> int:
    """Pretty-print a JSON file with 2-space indentation."""
    p = Path(path)
    if not p.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(data, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSON utilities")
    sub = parser.add_subparsers(dest="command")

    p_parse = sub.add_parser("parse", help="show top-level keys and types")
    p_parse.add_argument("file", help="path to JSON file")

    p_fmt = sub.add_parser("format", help="pretty-print JSON")
    p_fmt.add_argument("file", help="path to JSON file")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "parse":
        return cmd_parse(args.file)
    elif args.command == "format":
        return cmd_format(args.file)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
