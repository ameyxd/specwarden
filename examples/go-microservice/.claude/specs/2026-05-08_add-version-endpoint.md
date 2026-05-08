# 2026-05-08_add-version-endpoint: Add /version endpoint to items service

**Created:** 2026-05-08T14:30:00+00:00
**Status:** completed
**Author:** Amey

## Assumptions
- The service uses chi as its router; adding a new route follows the existing pattern.
- The version string is a compile-time constant defined in `main.go`; no build-flag
  injection is required for now.
- The `/health` endpoint already exists and can serve as the structural template.

## Scope
- Add a `GET /version` route in `main.go` that returns `{"version": "<semver>"}`.
- Define a `versionResponse` struct and a `serviceVersion` constant in `main.go`.
- No new files are required.

## Non-goals
- We will not expose build metadata (git SHA, build date) at this time.
- We will not add authentication or rate-limiting to the version endpoint.
- We will not move the version constant to a separate `version.go` file.

## Success criteria
- [x] `GET /version` returns HTTP 200 with `Content-Type: application/json`.
- [x] The response body is `{"version":"0.4.0"}` (or whatever the constant is set to).
- [x] Existing `/health` and `/items` endpoints are unaffected.
- [x] The service compiles without errors.
