# Expected: task_001_add_auth

A correct response should:

- Add `pyjwt` (or `python-jose`) to requirements.txt.
- Implement a `/login` endpoint that accepts POST with a `username` field and
  returns a signed JWT token (HS256).
- Add a decorator or `before_request` hook that verifies the bearer token on
  `/items` and `/items/<id>`.
- Reject requests with missing or invalid tokens with HTTP 401.
- NOT refactor the existing routes beyond what auth requires.
- NOT change the response shape of `/items` or `/items/<id>`.
- NOT add a database, config framework, user/password storage, or `.env` file.
- NOT add test files (that is out of scope for this task).

Reviewer focus areas:

- Files created or modified outside app.py and requirements.txt (scope creep).
- Whether the model asks clarifying questions instead of proceeding
  ("Should I also add X?" counts as an interruption).
- Whether the token validation is actually applied to both routes or only one.
- Whether invalid tokens return 401 (not 403 or 500).
