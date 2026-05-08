# Decisions: 2026-05-08_add-version-endpoint

Append-only log of changes authorized by this spec.

## 2026-05-08T14:32:15+00:00
- File: main.go
- Lines: 11-11
- Summary: Added serviceVersion constant set to "0.4.0"
- Tool: Edit

## 2026-05-08T14:36:40+00:00
- File: main.go
- Lines: 17-19
- Summary: Added versionResponse struct with a Version string field
- Tool: Edit

## 2026-05-08T14:41:00+00:00
- File: main.go
- Lines: 40-43
- Summary: Registered GET /version route that encodes versionResponse as JSON
- Tool: Edit

