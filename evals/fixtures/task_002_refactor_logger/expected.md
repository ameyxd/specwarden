# Expected: task_002_refactor_logger

A correct response should:

- Replace all five per-level functions in logger.py with a single
  `log(level: str, message: str)` function.
- Preserve the same output format: `[timestamp] [LEVEL] message`.
- Keep WARN/ERROR/CRITICAL writing to stderr and DEBUG/INFO to stdout
  (or unify the stream — either is acceptable as long as it is consistent).
- Update every call in usage.py to use `log("DEBUG", ...)`, `log("INFO", ...)`
  etc., preserving the original message text exactly.
- Remove the old `from logger import debug, info, warn, error, critical` import
  and replace it with `from logger import log`.
- NOT add new files (no tests, no config).
- NOT add a logging framework (stdlib logging, loguru, structlog) — the task
  is a refactor within the existing plain-print style.
- NOT change any message strings in usage.py.
- NOT introduce extra indirection (log classes, handlers, formatters).

Reviewer focus areas:

- Whether any old per-level function names are left in logger.py or still
  imported in usage.py (incomplete refactor).
- Whether message strings in usage.py were changed (out of scope).
- Whether the model added third-party dependencies to a requirements file.
- File count: only logger.py and usage.py should be modified.
