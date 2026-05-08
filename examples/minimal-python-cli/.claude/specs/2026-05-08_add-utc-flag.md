# 2026-05-08_add-utc-flag: Add --utc flag to date CLI

**Created:** 2026-05-08T12:00:00+00:00
**Status:** completed
**Author:** Amey

## Assumptions
- The CLI uses Python's stdlib `datetime` module; no third-party timezone library is present.
- Users currently see local-time output from the `now` subcommand.
- The existing `--fmt` option should continue to work unchanged whether or not `--utc` is set.

## Scope
- Add a `--utc` boolean flag to the `now` subcommand in `cli.py`.
- When the flag is set, obtain the timestamp via `datetime.now(timezone.utc)` instead of `datetime.now()`.
- Update the `README.md` usage block to show the new flag.

## Non-goals
- We will not add arbitrary timezone selection (e.g. `--tz America/New_York`).
- We will not refactor the existing local-time path or change its default behaviour.
- We will not add a `--utc` flag to any other subcommand at this time.

## Success criteria
- [x] `python cli.py now --utc` prints a UTC timestamp.
- [x] `python cli.py now` continues to print local time unchanged.
- [x] The `--fmt` flag composes correctly with `--utc`.
- [x] README documents the new flag with an example invocation.
