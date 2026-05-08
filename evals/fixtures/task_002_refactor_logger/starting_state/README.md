# Logger

A small logging utility module with per-level helper functions (`debug`,
`info`, `warn`, `error`, `critical`). The helpers are inconsistent — some
flush, some write to stderr, one adds a separator line.

The goal is to unify them into a single `log(level, message)` function.
