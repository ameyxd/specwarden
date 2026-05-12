# Releasing spec-trace

## One-time setup

1. Configure PyPI Trusted Publishing for this project at
   https://pypi.org/manage/account/publishing/. Use:
   - Owner: `<github-org-or-user>`
   - Repository: `spec-trace`
   - Workflow: `release.yml`
   - Environment: `pypi`
2. Create the `pypi` GitHub Environment under
   Settings -> Environments. No secrets are needed.

## Cutting a release

1. Bump `version` in `pyproject.toml`.
2. Update `src/spec_trace/__init__.py`'s `__version__` to match.
3. Commit on `main`:
   ```bash
   git commit -am "chore: release 0.1.1"
   ```
4. Tag without the `v` prefix:
   ```bash
   git tag 0.1.1
   git push origin main 0.1.1
   ```
5. Watch `.github/workflows/release.yml` run. The `test`, `build`, and
   `publish` jobs run in sequence. Publication is gated on tests + lint
   passing.

## Pre-releases

Tag as `0.2.0rc1`, etc. Same workflow path. PyPI's release page will
mark these as pre-releases automatically.

## Rolling back

PyPI does not allow re-uploading the same version. If a release is
broken, yank the bad version on PyPI (still keeps the file but hides
it from `pip install`), then publish a new patch version with the fix.

## Smoke test after release

```bash
pipx install spec-trace==0.1.1
cd /tmp && mkdir test && cd test && git init -q
spec-trace init
spec-trace new "Smoke test" --author you
```

If those commands run, the published wheel is intact.
