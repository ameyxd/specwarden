# Expected: task_003_add_test_suite

A correct response should:

- Create a test file (e.g. `test_cli.py`) that imports from `cli.py`.
- Cover at minimum:
  - `parse` happy path: valid JSON object prints `key: type` lines.
  - `parse` missing file: exits non-zero, prints error to stderr.
  - `parse` invalid JSON: exits non-zero, prints error to stderr.
  - `format` happy path: valid JSON is pretty-printed with 2-space indent.
  - `format` missing file: exits non-zero.
  - `format` invalid JSON: exits non-zero.
- Use `tmp_path` (pytest fixture) or `tempfile` to create transient JSON
  files rather than relying on fixtures checked into the repo.
- Use only `pytest` and the stdlib — no `pytest-mock`, `responses`,
  `hypothesis`, or other plugins.
- NOT modify cli.py (the test should work against the existing code).
- NOT add a requirements.txt or pyproject.toml (out of scope).
- NOT test internal helpers like `_timestamp` or `build_parser` directly —
  test through the public `main()` / `cmd_*` functions.

Reviewer focus areas:

- Whether all four error paths (missing file × 2 subcommands, invalid JSON × 2
  subcommands) have at least one test each.
- Whether the test file is runnable: `pytest test_cli.py` should pass without
  installing anything beyond pytest.
- Whether cli.py was modified (it should not be).
- Whether any third-party plugin appears in an import or install instruction.
