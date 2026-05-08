# counter

A shared counter incremented by multiple threads. The `inc()` method has a
documented race condition: the read-modify-write is not atomic, so the final
value is almost always less than `4 * n` when run with multiple threads.

## Running

```
python counter.py
```

The printed value will typically be less than 4000 (the expected result for
the default n=1000 across 4 threads).
