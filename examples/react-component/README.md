# Example: React component with spec-trace

This example shows what a small frontend repo looks like after a UI feature
has been authored under spec-trace. The feature is a "Reset" button added to
a stateful Counter component.

## What to look at, in order

1. `.claude/specs/2026-05-08_add-reset-button.md` — the spec written before
   any code was touched. The Non-goals section explicitly ruled out a
   confirmation dialog and an `onReset` callback, keeping the change minimal.
2. `Counter.tsx` — the implementation. The reset button calls `setCount(initial)`,
   which requires `initial` to be accessible in the component body.
3. `Counter.test.tsx` — a single focused test: increment twice, reset, assert
   the value returned to the initial prop.
4. `.claude/decisions/2026-05-08_add-reset-button.md` — the append-only log
   showing the three edits made under this spec, in order, with timestamps.

## Running the tests

```
npm install
npm test
```

In a real repo you would also see commits with a `Spec: 2026-05-08_add-reset-button`
trailer; git history is omitted here to keep the example focused on the
artifacts spec-trace produces.
