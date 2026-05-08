counter.py has a race condition documented in the comment inside inc(). Fix
it without changing the public API (start_workers, final_value). Then add a
test that exercises the fix: run start_workers with a high iteration count
and assert that final_value equals the expected total.
