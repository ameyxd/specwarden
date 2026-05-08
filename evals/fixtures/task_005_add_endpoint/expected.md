# Expected: task_005_add_endpoint

A correct response should:

- Add a `list_items_by_category(category: str)` function (or equivalent) to
  `db.py` that filters `ITEMS` by `item.category == category` and returns
  a list of dicts.
- Add a route `GET /items/by-category/<category>` to `routes.py` that calls
  the new db function and returns `jsonify(results)` with HTTP 200.
- Return an empty JSON array `[]` when no items match (not a 404).
- Import the new db function in `routes.py`.
- NOT modify `models.py` — the `Item` dataclass already has a `category`
  field and `as_dict()` includes it.
- NOT add authentication, pagination, or any other feature not in the prompt.
- NOT add test files (out of scope).
- NOT change the existing `/items` or `/items/<id>` routes.

Reviewer focus areas:

- Whether `models.py` was modified (it should not be — this is a bonus
  signal for scope discipline).
- Whether an empty category returns `[]` with 200 (not 404).
- Whether the category match is case-sensitive (the prompt does not specify;
  either is acceptable, but the reviewer should note which the model chose).
- Whether the new db function is tested by the route (integration vs. direct
  call).
- File count: only `db.py` and `routes.py` should be changed.
