# 2026-05-08_add-reset-button: Add reset button to Counter component

**Created:** 2026-05-08T09:15:00+00:00
**Status:** completed
**Author:** Amey

## Assumptions
- The Counter component manages its own count state via `useState`.
- The component receives an `initial` prop that sets the starting value.
- The existing increment and decrement buttons should not be changed.

## Scope
- Add a "Reset" `<button>` inside `Counter.tsx` that calls `setCount(initial)`.
- Add a test in `Counter.test.tsx` verifying that clicking Reset restores the
  initial value after the count has been modified.

## Non-goals
- We will not add a confirmation dialog before resetting.
- We will not persist reset history or expose an `onReset` callback at this time.
- We will not change the visual layout of the existing increment/decrement buttons.

## Success criteria
- [x] A "Reset" button appears in the rendered component.
- [x] Clicking Reset after incrementing returns the displayed value to `initial`.
- [x] Clicking Reset when already at the initial value is a no-op (no crash, no change).
- [x] The test suite passes.
