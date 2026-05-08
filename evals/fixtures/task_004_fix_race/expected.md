# Expected: task_004_fix_race

A correct response should:

- Fix the race in `Counter.inc()` using `threading.Lock` (or
  `threading.RLock`, or by using an `atomic`-style approach such as
  `threading.local` — but a plain lock is the canonical answer).
- NOT change the signatures of `start_workers(c, n)` or `final_value(c)`.
- NOT change the `Counter.__init__` signature.
- Add a test (e.g. `test_counter.py`) that:
  - Calls `start_workers` with at least n=500 or higher.
  - Asserts `final_value(c) == 4 * n` (the exact expected total).
  - Is deterministic — the test must pass every time, not just most of the time.
- NOT add third-party libraries (no `atomics`, no `multiprocessing`).
- NOT rewrite the threading model (e.g. replacing threads with
  `concurrent.futures` is out of scope unless the public API is unchanged).

Reviewer focus areas:

- Whether the fix is actually correct: running `python counter.py` 10 times
  should always print 4000.
- Whether the test asserts the exact value `4 * n` (a probabilistic assertion
  like `>= 3900` does not count).
- Whether `start_workers` or `final_value` signatures were changed.
- Whether any import outside stdlib was added.
