# Example: Go microservice with specwarden

This example shows what a small Go HTTP service looks like after a feature
has been authored under specwarden. The feature is a `GET /version` endpoint
added to a chi-based service that already has `/health` and `/items`.

## What to look at, in order

1. `.claude/specs/2026-05-08_add-version-endpoint.md` — the spec written before
   any code was touched. The Assumptions section notes that `/health` can serve
   as a structural template; the Non-goals section explicitly defers build
   metadata (git SHA, build date) to a later change.
2. `main.go` — the implementation. Three additions: a constant, a response
   struct, and a route registration. Everything else is untouched.
3. `.claude/decisions/2026-05-08_add-version-endpoint.md` — the append-only
   log showing each of the three edits in order, with timestamps.

## Running locally

```
go mod tidy
go run .
curl http://localhost:8080/version
# {"version":"0.4.0"}
curl http://localhost:8080/health
# {"status":"ok"}
```

In a real repo you would also see commits with a `Spec: 2026-05-08_add-version-endpoint`
trailer; git history is omitted here to keep the example focused on the
artifacts specwarden produces.
