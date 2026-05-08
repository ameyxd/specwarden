# Decisions: 2026-05-08_add-utc-flag

Append-only log of changes authorized by this spec.

## 2026-05-08T12:01:30+00:00
- File: cli.py
- Lines: 14-16
- Summary: Added --utc click.option to the now() command signature
- Tool: Edit

## 2026-05-08T12:05:10+00:00
- File: cli.py
- Lines: 19-24
- Summary: Branched on the utc flag to select datetime.now(timezone.utc) vs datetime.now()
- Tool: Edit

## 2026-05-08T12:09:45+00:00
- File: README.md
- Lines: 18-26
- Summary: Documented the --utc flag with example invocations in the usage section
- Tool: Edit

