"""A simple shared counter that races. Fix the race without changing the
public API (start_workers + final_value).
"""
import threading


class Counter:
    def __init__(self):
        self.value = 0

    def inc(self):
        # RACE: read-modify-write is not atomic.
        current = self.value
        self.value = current + 1


def start_workers(c: "Counter", n: int = 1000) -> None:
    """Spawn 4 threads, each calling c.inc() n times."""
    threads = [
        threading.Thread(target=lambda: [c.inc() for _ in range(n)])
        for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def final_value(c: "Counter") -> int:
    """Return the counter's current value."""
    return c.value


if __name__ == "__main__":
    c = Counter()
    start_workers(c)
    print(final_value(c))
