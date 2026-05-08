# Example: minimal Python CLI with spec-trace

This example shows what a small repo looks like after a feature has been
authored under spec-trace. The feature is a `--utc` flag for the `now`
subcommand of a Click-based date utility.

## What to look at, in order

1. `.claude/specs/2026-05-08_add-utc-flag.md` — the spec written before
   any code was touched. Note the four sections: Assumptions, Scope,
   Non-goals, Success criteria.
2. `cli.py` — the implementation. The change is small: one new option and a
   two-branch conditional. The spec kept it that way by naming what was
   out of scope.
3. `.claude/decisions/2026-05-08_add-utc-flag.md` — the append-only log
   that captures every edit made under this spec, with timestamps and line
   ranges.

## Usage

```
python cli.py now
python cli.py now --utc
python cli.py now --utc --fmt "%Y/%m/%d %H:%M"
python cli.py parse 2026-01-15T09:30:00
```

In a real repo you would also see commits with a `Spec: 2026-05-08_add-utc-flag`
trailer; git history is omitted here to keep the example focused on the
artifacts spec-trace produces.
