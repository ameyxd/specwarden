# spec-trace v1 implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship spec-trace v1 — a Claude Code skill, three lifecycle hooks, and a Python CLI that gate filesystem edits behind a written spec, plus a reproducible three-arm eval, install scripts, examples, and a launch-ready README.

**Architecture:** Three loosely coupled pieces sharing one synchronization point.
1. A Python CLI (`spec-trace`, packaged as `pipx install spec-trace`) handles spec creation, activation, coverage reporting, and lineage tracing.
2. Three hook scripts (`pre_tool_use.py`, `post_tool_use.py`, `session_start.py`) read the active-spec marker and append to a structured decisions log.
3. A `SKILL.md` exposes four slash commands (`/spec`, `/trace`, `/coverage`, `/spec-help`) that delegate to the CLI.
The synchronization point is a single-line file at `.claude/specs/active`. Spec coverage on commits is detected via a `Spec: <id>` trailer added by an optional `prepare-commit-msg` git hook.

**Tech Stack:** Python 3.10+, Typer (CLI), pytest (tests), ruff (lint + format), Bash + PowerShell installers, GitHub Actions (CI + release).

**Source of truth for v1 scope:** `SPEC_spec-trace.md` at the repo root. If this plan disagrees with the SPEC, the SPEC wins; raise the conflict before deviating.

---

## File structure

These are the files this plan creates or modifies. Each one has a single responsibility.

### Package source (`src/spec_trace/`)

| File | Responsibility |
| --- | --- |
| `__init__.py` | Package version + public re-exports. |
| `paths.py` | Resolves `.claude/` paths from a repo root. Pure functions, no I/O side effects beyond reading. |
| `spec.py` | Create, list, activate, complete a spec. Owns `.claude/specs/`. |
| `decisions.py` | Append entries to the decisions log. Owns `.claude/decisions/`. |
| `coverage.py` | Compute spec coverage over the last N commits via the `Spec:` trailer. |
| `trace.py` | Walk a commit → its spec → its decisions log. |
| `git_hook.py` | Install / uninstall the `prepare-commit-msg` git hook. |
| `cli.py` | Typer app exposing `init`, `new`, `activate`, `done`, `coverage`, `trace`, `status`. |

### Standalone hook scripts (`hooks/`)

| File | Responsibility |
| --- | --- |
| `pre_tool_use.py` | Reads stdin JSON; if no active spec, returns `permissionDecision: ask`. Otherwise records a pending entry. |
| `post_tool_use.py` | Reads stdin JSON + the pending entry; appends a finalized record to the decisions log. |
| `session_start.py` | Prints the active spec (if any) at session start; otherwise prints a reminder. |

These scripts must be self-contained — they may not import `spec_trace` because the user repo may not have it installed. Duplicate the small amount of path/IO logic they need.

### Skill artifact (`.claude/skills/spec-trace/`)

| File | Responsibility |
| --- | --- |
| `SKILL.md` | Skill definition; enumerates the four slash commands. |
| `scripts/new_spec.py`, `activate_spec.py`, `coverage.py`, `trace.py` | Slash-command shims that shell out to the installed CLI. |
| `templates/spec.md.template` | The canonical four-section spec template. |
| `templates/decision_entry.md.template` | The decisions-log entry shape. |

### Tests (`tests/`)

Mirror the source layout: `tests/test_paths.py`, `tests/test_spec.py`, etc.

### Eval suite (`evals/`)

| Path | Responsibility |
| --- | --- |
| `fixtures/task_00{1..5}_*/` | Frozen starting states + prompts. |
| `run_eval.py` | Spawns Claude Code in headless mode for each (arm × task) pair. |
| `measure.py` | Parses session logs, emits CSV + markdown scorecard. |
| `results/2026-05-XX.md` | Initial published results. |

### Top-level

| File | Responsibility |
| --- | --- |
| `pyproject.toml` | Package metadata, deps, Typer entry point. |
| `install.sh`, `install.ps1` | One-liner installers. |
| `Makefile` | Convenience targets (`make eval`, `make test`, `make lint`). |
| `.github/workflows/ci.yml`, `release.yml` | CI + PyPI release on tag. |
| `README.md` | Published landing page. Last to land. |
| `LICENSE` | MIT. |

---

## Phase 0 — Bootstrap

Goal: a working Python project skeleton with tests passing, lint clean, CI green. No spec-trace logic yet.

### Task 0.1: Initialize git and write `pyproject.toml`

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `Makefile`

- [ ] **Step 1: Initialize the repo**

```bash
cd /Users/amey/Documents/projects/spectrace
git init -b main
git add CLAUDE.md SPEC_spec-trace.md .gitignore
git commit -m "chore: initial commit with spec and standing notes"
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spec-trace"
version = "0.1.0"
description = "Force a written spec before any code change. Logs every edit with a backlink."
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [{ name = "Amey Ambade", email = "ameyambade@gmail.com" }]
dependencies = [
    "typer>=0.12,<1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.5",
]

[project.scripts]
spec-trace = "spec_trace.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/spec_trace"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"

[tool.ruff]
line-length = 100
target-version = "py310"
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "PTH"]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.format]
quote-style = "double"
```

- [ ] **Step 3: Write a placeholder `README.md` so `pyproject.toml` builds**

```markdown
# spec-trace

Force a written spec before any code change. Logs every edit with a backlink.

This README is a placeholder. The launch-ready README lands in Phase 11.
See `SPEC_spec-trace.md` for the full v1 scope.
```

- [ ] **Step 4: Add MIT `LICENSE`**

Use the standard MIT text with `Copyright (c) 2026 Amey Ambade`.

- [ ] **Step 5: Add a minimal `Makefile`**

```makefile
.PHONY: test lint fmt eval install-dev

install-dev:
	pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff format .
	ruff check --fix .

eval:
	python evals/run_eval.py
```

- [ ] **Step 6: Verify the build succeeds**

Run: `pip install -e '.[dev]'`
Expected: install completes, `spec-trace --help` runs (and currently fails because `cli.py` does not exist yet — that's fine, we wire it in Phase 4; for now confirm `pip install` itself succeeds).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml LICENSE Makefile README.md
git commit -m "chore: bootstrap python package metadata"
```

### Task 0.2: Scaffold `src/spec_trace/` and `tests/`

**Files:**
- Create: `src/spec_trace/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Create the package**

```python
# src/spec_trace/__init__.py
"""spec-trace: spec-first discipline for Claude Code, with teeth."""

__version__ = "0.1.0"
```

- [ ] **Step 2: Create the tests package**

```python
# tests/__init__.py
```

(empty file — pytest discovers either way, but this keeps imports tidy)

- [ ] **Step 3: Write a smoke test**

```python
# tests/test_smoke.py
from spec_trace import __version__


def test_version_is_a_string():
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2
```

- [ ] **Step 4: Run it**

Run: `pytest`
Expected: 1 passed.

- [ ] **Step 5: Run lint**

Run: `ruff check . && ruff format --check .`
Expected: clean. If format complains, run `make fmt` and re-run.

- [ ] **Step 6: Commit**

```bash
git add src tests
git commit -m "chore: scaffold package and smoke test"
```

### Task 0.3: Add CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the CI workflow**

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e '.[dev]'
      - run: ruff check .
      - run: ruff format --check .
      - run: pytest --cov=spec_trace --cov-report=term-missing
```

- [ ] **Step 2: Commit**

```bash
git add .github
git commit -m "ci: add lint + test matrix"
```

---

## Phase 1 — CLI: spec lifecycle

Goal: `spec-trace init`, `new`, `activate`, `done` work end-to-end against the filesystem. No git, no commit trailers yet.

### Task 1.1: `paths.py` — resolve `.claude/` layout

**Files:**
- Create: `src/spec_trace/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_paths.py
from pathlib import Path

from spec_trace.paths import RepoPaths


def test_repo_paths_under_root(tmp_path: Path):
    p = RepoPaths(tmp_path)
    assert p.specs_dir == tmp_path / ".claude" / "specs"
    assert p.decisions_dir == tmp_path / ".claude" / "decisions"
    assert p.active_marker == tmp_path / ".claude" / "specs" / "active"


def test_ensure_dirs_creates_layout(tmp_path: Path):
    p = RepoPaths(tmp_path)
    p.ensure_dirs()
    assert p.specs_dir.is_dir()
    assert p.decisions_dir.is_dir()


def test_active_spec_id_returns_none_when_unset(tmp_path: Path):
    p = RepoPaths(tmp_path)
    p.ensure_dirs()
    assert p.active_spec_id() is None


def test_active_spec_id_strips_whitespace(tmp_path: Path):
    p = RepoPaths(tmp_path)
    p.ensure_dirs()
    p.active_marker.write_text("  2026-05-07_demo \n", encoding="utf-8")
    assert p.active_spec_id() == "2026-05-07_demo"
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_paths.py -v`
Expected: ImportError on `RepoPaths`.

- [ ] **Step 3: Implement `paths.py`**

```python
# src/spec_trace/paths.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoPaths:
    """Resolve the .claude/ layout under a repo root."""

    root: Path

    @property
    def claude_dir(self) -> Path:
        return self.root / ".claude"

    @property
    def specs_dir(self) -> Path:
        return self.claude_dir / "specs"

    @property
    def decisions_dir(self) -> Path:
        return self.claude_dir / "decisions"

    @property
    def active_marker(self) -> Path:
        return self.specs_dir / "active"

    def ensure_dirs(self) -> None:
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)

    def active_spec_id(self) -> str | None:
        if not self.active_marker.exists():
            return None
        text = self.active_marker.read_text(encoding="utf-8").strip()
        return text or None
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_paths.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/spec_trace/paths.py tests/test_paths.py
git commit -m "feat: add RepoPaths to resolve .claude/ layout"
```

### Task 1.2: `spec.py` — create + activate

**Files:**
- Create: `src/spec_trace/spec.py`
- Create: `tests/test_spec.py`

The spec ID format is `YYYY-MM-DD_<slug>`. Slugs are lowercased, spaces become hyphens, only `[a-z0-9-]` survive. Date comes from a callable so tests can pin it.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_spec.py
from datetime import date
from pathlib import Path

import pytest

from spec_trace.paths import RepoPaths
from spec_trace.spec import (
    SpecAlreadyExists,
    SpecNotFound,
    activate_spec,
    create_spec,
    deactivate_active,
    slugify,
)


def fixed_date() -> date:
    return date(2026, 5, 7)


def test_slugify_normalizes_input():
    assert slugify("Add JWT Auth!") == "add-jwt-auth"
    assert slugify("  Refactor  Logger  ") == "refactor-logger"


def test_create_spec_writes_file(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()

    spec_id = create_spec(paths, "Add JWT Auth", author="Amey", today=fixed_date)

    assert spec_id == "2026-05-07_add-jwt-auth"
    spec_file = paths.specs_dir / f"{spec_id}.md"
    assert spec_file.exists()
    body = spec_file.read_text(encoding="utf-8")
    assert "## Assumptions" in body
    assert "## Scope" in body
    assert "## Non-goals" in body
    assert "## Success criteria" in body
    assert "Author: Amey" in body or "**Author:** Amey" in body


def test_create_spec_refuses_duplicate(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    create_spec(paths, "demo", author="A", today=fixed_date)
    with pytest.raises(SpecAlreadyExists):
        create_spec(paths, "demo", author="A", today=fixed_date)


def test_activate_sets_marker(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    spec_id = create_spec(paths, "demo", author="A", today=fixed_date)

    activate_spec(paths, spec_id)

    assert paths.active_spec_id() == spec_id


def test_activate_unknown_spec_raises(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    with pytest.raises(SpecNotFound):
        activate_spec(paths, "2026-05-07_does-not-exist")


def test_deactivate_clears_marker(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    spec_id = create_spec(paths, "demo", author="A", today=fixed_date)
    activate_spec(paths, spec_id)

    deactivate_active(paths)

    assert paths.active_spec_id() is None
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_spec.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `spec.py`**

```python
# src/spec_trace/spec.py
from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime, timezone

from .paths import RepoPaths


class SpecError(Exception):
    """Base class for spec lifecycle errors."""


class SpecAlreadyExists(SpecError):
    pass


class SpecNotFound(SpecError):
    pass


_SLUG_KEEP = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    collapsed = _SLUG_KEEP.sub("-", lowered)
    return collapsed.strip("-")


def _today() -> date:
    return datetime.now(timezone.utc).date()


SPEC_TEMPLATE = """\
# {spec_id}: {title}

**Created:** {created}
**Status:** active
**Author:** {author}

## Assumptions
What we are taking as given. If any of these turns out to be false, the spec is invalid and must be revised before more code lands.

- TODO

## Scope
What this change is. Concrete, files-and-functions level if possible.

- TODO

## Non-goals
What this change is explicitly not. The point of this section is to prevent scope creep mid-implementation.

- TODO

## Success criteria
How we will know we are done. Must be checkable.

- [ ] TODO
"""


def create_spec(
    paths: RepoPaths,
    title: str,
    *,
    author: str,
    today: Callable[[], date] = _today,
) -> str:
    paths.ensure_dirs()
    slug = slugify(title)
    if not slug:
        raise SpecError("title produced an empty slug")
    spec_id = f"{today().isoformat()}_{slug}"
    spec_file = paths.specs_dir / f"{spec_id}.md"
    if spec_file.exists():
        raise SpecAlreadyExists(spec_id)
    body = SPEC_TEMPLATE.format(
        spec_id=spec_id,
        title=title,
        created=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        author=author,
    )
    spec_file.write_text(body, encoding="utf-8")
    return spec_id


def activate_spec(paths: RepoPaths, spec_id: str) -> None:
    spec_file = paths.specs_dir / f"{spec_id}.md"
    if not spec_file.exists():
        raise SpecNotFound(spec_id)
    paths.ensure_dirs()
    paths.active_marker.write_text(spec_id + "\n", encoding="utf-8")


def deactivate_active(paths: RepoPaths) -> None:
    if paths.active_marker.exists():
        paths.active_marker.unlink()
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_spec.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/spec_trace/spec.py tests/test_spec.py
git commit -m "feat: spec creation, activation, and deactivation"
```

### Task 1.3: `spec.py` — `mark_done` flips status to completed

**Files:**
- Modify: `src/spec_trace/spec.py`
- Modify: `tests/test_spec.py`

- [ ] **Step 1: Add the failing test**

```python
def test_mark_done_flips_status_and_clears_marker(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    spec_id = create_spec(paths, "demo", author="A", today=fixed_date)
    activate_spec(paths, spec_id)

    from spec_trace.spec import mark_done

    mark_done(paths)

    assert paths.active_spec_id() is None
    body = (paths.specs_dir / f"{spec_id}.md").read_text(encoding="utf-8")
    assert "**Status:** completed" in body
```

- [ ] **Step 2: Run, watch it fail**

Run: `pytest tests/test_spec.py -v`
Expected: 1 failure (no `mark_done`).

- [ ] **Step 3: Implement `mark_done`**

Add to `spec.py`:

```python
def mark_done(paths: RepoPaths) -> str:
    spec_id = paths.active_spec_id()
    if spec_id is None:
        raise SpecNotFound("no active spec")
    spec_file = paths.specs_dir / f"{spec_id}.md"
    text = spec_file.read_text(encoding="utf-8")
    updated = text.replace("**Status:** active", "**Status:** completed", 1)
    spec_file.write_text(updated, encoding="utf-8")
    deactivate_active(paths)
    return spec_id
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_spec.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git commit -am "feat: mark_done flips status and clears marker"
```

---

## Phase 2 — Decisions log

Goal: a structured, append-only log per spec.

### Task 2.1: `decisions.py`

**Files:**
- Create: `src/spec_trace/decisions.py`
- Create: `tests/test_decisions.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_decisions.py
from datetime import datetime, timezone
from pathlib import Path

from spec_trace.decisions import DecisionEntry, append_decision
from spec_trace.paths import RepoPaths


def fixed_now() -> datetime:
    return datetime(2026, 5, 7, 14, 32, 18, tzinfo=timezone.utc)


def test_append_creates_log_with_header(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    entry = DecisionEntry(
        file_path="src/auth/jwt.py",
        line_range="1-87 (created)",
        summary="Initial JWT verification middleware",
        tool="Write",
    )

    append_decision(paths, "2026-05-07_add-auth", entry, now=fixed_now)

    log = paths.decisions_dir / "2026-05-07_add-auth.md"
    text = log.read_text(encoding="utf-8")
    assert text.startswith("# Decisions: 2026-05-07_add-auth")
    assert "## 2026-05-07T14:32:18+00:00" in text
    assert "- File: src/auth/jwt.py" in text
    assert "- Lines: 1-87 (created)" in text
    assert "- Summary: Initial JWT verification middleware" in text
    assert "- Tool: Write" in text


def test_append_is_appendonly(tmp_path: Path):
    paths = RepoPaths(tmp_path)
    paths.ensure_dirs()
    e1 = DecisionEntry("a.py", "1-5", "first", "Edit")
    e2 = DecisionEntry("b.py", "1-5", "second", "Edit")

    append_decision(paths, "spec1", e1, now=fixed_now)
    append_decision(paths, "spec1", e2, now=fixed_now)

    text = (paths.decisions_dir / "spec1.md").read_text(encoding="utf-8")
    assert text.count("## 2026-05-07T14:32:18+00:00") == 2
    assert text.index("first") < text.index("second")
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_decisions.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `decisions.py`**

```python
# src/spec_trace/decisions.py
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from .paths import RepoPaths


@dataclass(frozen=True)
class DecisionEntry:
    file_path: str
    line_range: str
    summary: str
    tool: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def append_decision(
    paths: RepoPaths,
    spec_id: str,
    entry: DecisionEntry,
    *,
    now: Callable[[], datetime] = _now,
) -> None:
    paths.ensure_dirs()
    log = paths.decisions_dir / f"{spec_id}.md"
    block = (
        f"## {now().isoformat(timespec='seconds')}\n"
        f"- File: {entry.file_path}\n"
        f"- Lines: {entry.line_range}\n"
        f"- Summary: {entry.summary}\n"
        f"- Tool: {entry.tool}\n\n"
    )
    if not log.exists():
        header = f"# Decisions: {spec_id}\n\nAppend-only log of changes authorized by this spec.\n\n"
        log.write_text(header + block, encoding="utf-8")
    else:
        with log.open("a", encoding="utf-8") as f:
            f.write(block)
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_decisions.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/spec_trace/decisions.py tests/test_decisions.py
git commit -m "feat: append-only decisions log per spec"
```

---

## Phase 3 — Coverage and trace

Goal: read git history and report which commits were authorized by a spec, and walk a commit back to its origin.

### Task 3.1: `coverage.py` — parse `Spec:` trailers

**Files:**
- Create: `src/spec_trace/coverage.py`
- Create: `tests/test_coverage.py`

- [ ] **Step 1: Write failing tests**

The trailer format is `Spec: <spec-id>` on its own line in the commit message body. Coverage walks `git log -n N --format=%H%x00%B%x00`.

```python
# tests/test_coverage.py
import subprocess
from pathlib import Path

import pytest

from spec_trace.coverage import CoverageReport, compute_coverage


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return out.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "f.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "first commit\n\nSpec: 2026-05-07_demo")
    (tmp_path / "f.txt").write_text("b")
    _git(tmp_path, "commit", "-q", "-am", "second commit, no spec")
    (tmp_path / "f.txt").write_text("c")
    _git(tmp_path, "commit", "-q", "-am", "third commit\n\nSpec: 2026-05-07_demo")
    return tmp_path


def test_compute_coverage_counts_trailers(repo: Path):
    report = compute_coverage(repo, last=10)

    assert isinstance(report, CoverageReport)
    assert report.total == 3
    assert report.covered == 2
    assert len(report.uncovered_hashes) == 1
    assert report.percentage == pytest.approx(2 / 3 * 100, rel=1e-3)


def test_compute_coverage_respects_last(repo: Path):
    report = compute_coverage(repo, last=2)
    assert report.total == 2
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_coverage.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `coverage.py`**

```python
# src/spec_trace/coverage.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_TRAILER = re.compile(r"^Spec:\s*(?P<id>\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class CoverageReport:
    total: int
    covered: int
    uncovered_hashes: list[str]

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return 100.0 * self.covered / self.total


def compute_coverage(repo: Path, *, last: int) -> CoverageReport:
    out = subprocess.run(
        ["git", "log", f"-n{last}", "--format=%H%x1f%B%x1e"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if not out:
        return CoverageReport(total=0, covered=0, uncovered_hashes=[])

    records = [r for r in out.split("\x1e") if r.strip()]
    total = 0
    covered = 0
    uncovered: list[str] = []
    for record in records:
        sha, _, body = record.partition("\x1f")
        sha = sha.strip()
        if not sha:
            continue
        total += 1
        if _TRAILER.search(body):
            covered += 1
        else:
            uncovered.append(sha)
    return CoverageReport(total=total, covered=covered, uncovered_hashes=uncovered)
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_coverage.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/spec_trace/coverage.py tests/test_coverage.py
git commit -m "feat: spec coverage via Spec: trailer in git log"
```

### Task 3.2: `trace.py` — commit → spec → decisions

**Files:**
- Create: `src/spec_trace/trace.py`
- Create: `tests/test_trace.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_trace.py
import subprocess
from pathlib import Path

import pytest

from spec_trace.trace import TraceResult, trace_commit


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "2026-05-07_demo.md").write_text("# spec body")
    (tmp_path / ".claude" / "decisions").mkdir()
    (tmp_path / ".claude" / "decisions" / "2026-05-07_demo.md").write_text("# log body")
    (tmp_path / "f.txt").write_text("a")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "covered commit\n\nSpec: 2026-05-07_demo")
    return tmp_path


def test_trace_returns_chain(repo: Path):
    sha = _git(repo, "rev-parse", "HEAD").strip()

    result = trace_commit(repo, sha)

    assert isinstance(result, TraceResult)
    assert result.commit_sha == sha
    assert result.spec_id == "2026-05-07_demo"
    assert "spec body" in result.spec_text
    assert "log body" in result.decisions_text


def test_trace_returns_none_when_no_trailer(repo: Path):
    (repo / "f.txt").write_text("b")
    _git(repo, "commit", "-q", "-am", "no trailer")
    sha = _git(repo, "rev-parse", "HEAD").strip()

    result = trace_commit(repo, sha)

    assert result.spec_id is None
    assert result.spec_text == ""
    assert result.decisions_text == ""
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_trace.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `trace.py`**

```python
# src/spec_trace/trace.py
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .paths import RepoPaths

_TRAILER = re.compile(r"^Spec:\s*(?P<id>\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class TraceResult:
    commit_sha: str
    spec_id: str | None
    spec_text: str
    decisions_text: str


def trace_commit(repo: Path, sha: str) -> TraceResult:
    body = subprocess.run(
        ["git", "log", "-1", "--format=%B", sha],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    match = _TRAILER.search(body)
    if not match:
        return TraceResult(commit_sha=sha, spec_id=None, spec_text="", decisions_text="")
    spec_id = match.group("id")
    paths = RepoPaths(repo)
    spec_file = paths.specs_dir / f"{spec_id}.md"
    log_file = paths.decisions_dir / f"{spec_id}.md"
    return TraceResult(
        commit_sha=sha,
        spec_id=spec_id,
        spec_text=spec_file.read_text(encoding="utf-8") if spec_file.exists() else "",
        decisions_text=log_file.read_text(encoding="utf-8") if log_file.exists() else "",
    )
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_trace.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/spec_trace/trace.py tests/test_trace.py
git commit -m "feat: trace_commit walks commit -> spec -> decisions"
```

---

## Phase 4 — Typer CLI

Goal: a working `spec-trace` binary that exposes the lifecycle.

### Task 4.1: `cli.py` — wire it together

**Files:**
- Create: `src/spec_trace/cli.py`
- Create: `tests/test_cli.py`

The CLI uses Typer's `CliRunner` for testing.

- [ ] **Step 1: Write failing tests for `init`, `new`, `activate`, `done`, `coverage`, `trace`, `status`**

```python
# tests/test_cli.py
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spec_trace.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_init_creates_layout(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(app, ["init", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".claude" / "specs").is_dir()
    assert (tmp_path / ".claude" / "decisions").is_dir()


def test_new_then_activate_then_done(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    r1 = runner.invoke(
        app, ["new", "Add JWT Auth", "--author", "Amey", "--root", str(tmp_path)]
    )
    assert r1.exit_code == 0, r1.stdout
    spec_id = r1.stdout.strip().split()[-1]

    r2 = runner.invoke(app, ["activate", spec_id, "--root", str(tmp_path)])
    assert r2.exit_code == 0, r2.stdout
    assert (tmp_path / ".claude" / "specs" / "active").read_text().strip() == spec_id

    r3 = runner.invoke(app, ["done", "--root", str(tmp_path)])
    assert r3.exit_code == 0, r3.stdout
    assert not (tmp_path / ".claude" / "specs" / "active").exists()


def test_status_reports_no_active(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    result = runner.invoke(app, ["status", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "no active spec" in result.stdout.lower()
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_cli.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `cli.py`**

```python
# src/spec_trace/cli.py
from __future__ import annotations

from pathlib import Path

import typer

from . import __version__
from .coverage import compute_coverage
from .decisions import DecisionEntry, append_decision
from .paths import RepoPaths
from .spec import (
    SpecError,
    activate_spec,
    create_spec,
    deactivate_active,
    mark_done,
)
from .trace import trace_commit

app = typer.Typer(add_completion=False, help="spec-trace: spec-first discipline, with teeth.")


def _root_option() -> Path:
    return typer.Option(Path.cwd(), "--root", help="Repo root.")


@app.command()
def init(root: Path = _root_option()) -> None:
    """Create the .claude/ layout in the current repo."""
    paths = RepoPaths(root)
    paths.ensure_dirs()
    typer.echo(f"initialized: {paths.claude_dir}")


@app.command("new")
def new_cmd(
    title: str,
    author: str = typer.Option(..., "--author", "-a"),
    root: Path = _root_option(),
) -> None:
    """Create a new spec from the four-section template."""
    paths = RepoPaths(root)
    try:
        spec_id = create_spec(paths, title, author=author)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"created spec {spec_id}")


@app.command()
def activate(spec_id: str, root: Path = _root_option()) -> None:
    """Mark a spec as the active one — subsequent edits get logged here."""
    paths = RepoPaths(root)
    try:
        activate_spec(paths, spec_id)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"active: {spec_id}")


@app.command()
def done(root: Path = _root_option()) -> None:
    """Mark the active spec as completed and clear the marker."""
    paths = RepoPaths(root)
    try:
        spec_id = mark_done(paths)
    except SpecError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"completed: {spec_id}")


@app.command()
def status(root: Path = _root_option()) -> None:
    """Print the active spec, if any."""
    paths = RepoPaths(root)
    spec_id = paths.active_spec_id()
    if spec_id is None:
        typer.echo("no active spec — run `spec-trace new <title>` to start.")
        return
    typer.echo(f"active: {spec_id}")


@app.command()
def coverage(
    last: int = typer.Option(50, "--last", "-n"),
    root: Path = _root_option(),
) -> None:
    """Report Spec: trailer coverage over the last N commits."""
    report = compute_coverage(root, last=last)
    typer.echo(
        f"{report.covered}/{report.total} commits have spec coverage "
        f"({report.percentage:.0f}%)"
    )
    if report.uncovered_hashes:
        typer.echo("uncovered:")
        for sha in report.uncovered_hashes:
            typer.echo(f"  {sha[:12]}")


@app.command()
def trace(commit: str = typer.Argument("HEAD"), root: Path = _root_option()) -> None:
    """Print the full chain (commit -> spec -> decisions)."""
    result = trace_commit(root, commit)
    typer.echo(f"commit: {result.commit_sha}")
    if result.spec_id is None:
        typer.echo("no Spec: trailer on this commit.")
        raise typer.Exit(code=1)
    typer.echo(f"spec:   {result.spec_id}")
    typer.echo("---")
    typer.echo(result.spec_text)
    typer.echo("---")
    typer.echo(result.decisions_text)


@app.command()
def version() -> None:
    typer.echo(__version__)
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_cli.py -v`
Expected: 3 passed.

- [ ] **Step 5: Smoke-test the binary**

```bash
spec-trace --help
spec-trace version
```

Expected: help output, then `0.1.0`.

- [ ] **Step 6: Commit**

```bash
git add src/spec_trace/cli.py tests/test_cli.py
git commit -m "feat: typer CLI with init, new, activate, done, status, coverage, trace"
```

---

## Phase 5 — `prepare-commit-msg` git hook

Goal: when a spec is active, every commit gets a `Spec: <id>` trailer added automatically. This is what makes coverage detection trivial.

### Task 5.1: `git_hook.py` — install / uninstall

**Files:**
- Create: `src/spec_trace/git_hook.py`
- Create: `tests/test_git_hook.py`
- Modify: `src/spec_trace/cli.py` — add `git-hook install` / `git-hook uninstall` subcommands.

The hook is a small bash script:

```bash
#!/usr/bin/env bash
# managed-by: spec-trace
set -e
COMMIT_MSG_FILE="$1"
ACTIVE_FILE="$(git rev-parse --show-toplevel)/.claude/specs/active"
if [ -f "$ACTIVE_FILE" ]; then
    SPEC_ID="$(tr -d '[:space:]' < "$ACTIVE_FILE")"
    if [ -n "$SPEC_ID" ] && ! grep -q "^Spec: $SPEC_ID$" "$COMMIT_MSG_FILE"; then
        printf "\nSpec: %s\n" "$SPEC_ID" >> "$COMMIT_MSG_FILE"
    fi
fi
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_git_hook.py
import os
import stat
import subprocess
from pathlib import Path

import pytest

from spec_trace.git_hook import install_hook, uninstall_hook


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    return tmp_path


def test_install_creates_executable_hook(repo: Path):
    install_hook(repo)
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    assert hook.is_file()
    assert hook.stat().st_mode & stat.S_IXUSR


def test_hook_appends_trailer_when_active(repo: Path):
    install_hook(repo)
    (repo / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    (repo / "f.txt").write_text("hi")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "do thing")

    body = _git(repo, "log", "-1", "--format=%B")
    assert "Spec: 2026-05-07_demo" in body


def test_hook_is_noop_when_no_active(repo: Path):
    install_hook(repo)
    (repo / "f.txt").write_text("hi")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "do thing")
    body = _git(repo, "log", "-1", "--format=%B")
    assert "Spec:" not in body


def test_uninstall_removes_managed_hook(repo: Path):
    install_hook(repo)
    uninstall_hook(repo)
    assert not (repo / ".git" / "hooks" / "prepare-commit-msg").exists()


def test_uninstall_preserves_unmanaged_hook(repo: Path):
    hook = repo / ".git" / "hooks" / "prepare-commit-msg"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho hand-written\n")
    os.chmod(hook, 0o755)

    uninstall_hook(repo)

    assert hook.exists()
    assert "hand-written" in hook.read_text()
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_git_hook.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `git_hook.py`**

```python
# src/spec_trace/git_hook.py
from __future__ import annotations

import os
import stat
from pathlib import Path

HOOK_SCRIPT = """\
#!/usr/bin/env bash
# managed-by: spec-trace
set -e
COMMIT_MSG_FILE="$1"
ACTIVE_FILE="$(git rev-parse --show-toplevel)/.claude/specs/active"
if [ -f "$ACTIVE_FILE" ]; then
    SPEC_ID="$(tr -d '[:space:]' < "$ACTIVE_FILE")"
    if [ -n "$SPEC_ID" ] && ! grep -q "^Spec: $SPEC_ID$" "$COMMIT_MSG_FILE"; then
        printf "\\nSpec: %s\\n" "$SPEC_ID" >> "$COMMIT_MSG_FILE"
    fi
fi
"""

MANAGED_MARKER = "# managed-by: spec-trace"


def _hook_path(repo: Path) -> Path:
    return repo / ".git" / "hooks" / "prepare-commit-msg"


def install_hook(repo: Path) -> Path:
    path = _hook_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and MANAGED_MARKER not in path.read_text(encoding="utf-8"):
        raise RuntimeError(
            "prepare-commit-msg hook already exists and was not installed by spec-trace; "
            "remove it manually or merge by hand."
        )
    path.write_text(HOOK_SCRIPT, encoding="utf-8")
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def uninstall_hook(repo: Path) -> None:
    path = _hook_path(repo)
    if not path.exists():
        return
    if MANAGED_MARKER in path.read_text(encoding="utf-8"):
        path.unlink()
```

- [ ] **Step 4: Tests pass**

Run: `pytest tests/test_git_hook.py -v`
Expected: 5 passed.

- [ ] **Step 5: Wire CLI subcommands**

Add to `cli.py`:

```python
git_hook_app = typer.Typer(help="Manage the prepare-commit-msg git hook.")
app.add_typer(git_hook_app, name="git-hook")


@git_hook_app.command("install")
def git_hook_install(root: Path = _root_option()) -> None:
    from .git_hook import install_hook
    path = install_hook(root)
    typer.echo(f"installed: {path}")


@git_hook_app.command("uninstall")
def git_hook_uninstall(root: Path = _root_option()) -> None:
    from .git_hook import uninstall_hook
    uninstall_hook(root)
    typer.echo("uninstalled.")
```

- [ ] **Step 6: Commit**

```bash
git add src/spec_trace/git_hook.py tests/test_git_hook.py src/spec_trace/cli.py
git commit -m "feat: prepare-commit-msg hook auto-adds Spec: trailer"
```

---

## Phase 6 — Claude Code lifecycle hooks

Goal: three standalone scripts in `hooks/` that the user repo's `.claude/settings.json` can point to. They must not depend on `spec_trace` being installed.

### Task 6.1: `pre_tool_use.py`

**Files:**
- Create: `hooks/pre_tool_use.py`
- Create: `tests/test_pre_tool_use.py`

Behavior:
- Reads JSON from stdin. The tool name is at `tool_name`.
- If `tool_name` not in `{"Edit", "Write"}`, return `{"permissionDecision": "allow"}` and exit 0.
- Else, read `<repo>/.claude/specs/active`. If empty/missing, return `{"permissionDecision": "ask", "message": "..."}` and exit 0.
- If active, return allow.
- Quick-fix mode: if env var `SPEC_TRACE_QUICKFIX=1`, allow regardless.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_pre_tool_use.py
import json
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre_tool_use.py"


def _run(payload: dict, cwd: Path, env: dict | None = None) -> dict:
    proc = subprocess.run(
        ["python", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_non_editing_tool_is_allowed(tmp_path: Path):
    out = _run({"tool_name": "Read"}, cwd=tmp_path)
    assert out["permissionDecision"] == "allow"


def test_edit_with_no_active_spec_is_asked(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert out["permissionDecision"] == "ask"
    assert "spec-trace" in out["message"].lower()


def test_edit_with_active_spec_is_allowed(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")
    out = _run({"tool_name": "Edit"}, cwd=tmp_path)
    assert out["permissionDecision"] == "allow"


def test_quickfix_env_overrides(tmp_path: Path, monkeypatch):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    import os
    env = os.environ.copy()
    env["SPEC_TRACE_QUICKFIX"] = "1"
    out = _run({"tool_name": "Write"}, cwd=tmp_path, env=env)
    assert out["permissionDecision"] == "allow"
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_pre_tool_use.py -v`
Expected: FileNotFoundError on the hook.

- [ ] **Step 3: Implement `hooks/pre_tool_use.py`**

```python
#!/usr/bin/env python3
"""spec-trace PreToolUse hook. Self-contained — no external imports."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _active_spec_id(repo: Path) -> str | None:
    marker = repo / ".claude" / "specs" / "active"
    if not marker.exists():
        return None
    text = marker.read_text(encoding="utf-8").strip()
    return text or None


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    tool = payload.get("tool_name", "")
    if tool not in EDITING_TOOLS:
        print(json.dumps({"permissionDecision": "allow"}))
        return 0

    if os.environ.get("SPEC_TRACE_QUICKFIX") == "1":
        print(json.dumps({"permissionDecision": "allow"}))
        return 0

    repo = Path.cwd()
    if _active_spec_id(repo) is None:
        print(
            json.dumps(
                {
                    "permissionDecision": "ask",
                    "message": (
                        "spec-trace: no active spec. Run `/spec <slug>` first to define "
                        "what you're building before editing files."
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"permissionDecision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Make it executable**

Run: `chmod +x hooks/pre_tool_use.py`

- [ ] **Step 5: Tests pass**

Run: `pytest tests/test_pre_tool_use.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add hooks/pre_tool_use.py tests/test_pre_tool_use.py
git commit -m "feat: PreToolUse hook gates Edit/Write on active spec"
```

### Task 6.2: `post_tool_use.py`

**Files:**
- Create: `hooks/post_tool_use.py`
- Create: `tests/test_post_tool_use.py`

Behavior:
- Reads JSON from stdin. Looks for `tool_name`, `tool_input.file_path`, optionally `tool_input.old_string` / `tool_input.content` to compute a one-line summary.
- If not editing, no-op.
- If active spec, append a `DecisionEntry` to `.claude/decisions/<spec-id>.md`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_post_tool_use.py
import json
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "post_tool_use.py"


def _run(payload: dict, cwd: Path) -> None:
    proc = subprocess.run(
        ["python", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    assert proc.returncode == 0, proc.stderr


def test_appends_decision_entry(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "decisions").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")

    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "src/auth/jwt.py", "content": "def verify(): pass\n" * 10},
    }
    _run(payload, cwd=tmp_path)

    log = (tmp_path / ".claude" / "decisions" / "2026-05-07_demo.md").read_text()
    assert "src/auth/jwt.py" in log
    assert "Tool: Write" in log


def test_noop_when_no_active(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "decisions").mkdir(parents=True)
    payload = {"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": "x"}}
    _run(payload, cwd=tmp_path)
    assert not list((tmp_path / ".claude" / "decisions").iterdir())
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_post_tool_use.py -v`
Expected: FileNotFoundError.

- [ ] **Step 3: Implement `hooks/post_tool_use.py`**

```python
#!/usr/bin/env python3
"""spec-trace PostToolUse hook. Self-contained."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EDITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _active_spec_id(repo: Path) -> str | None:
    marker = repo / ".claude" / "specs" / "active"
    if not marker.exists():
        return None
    text = marker.read_text(encoding="utf-8").strip()
    return text or None


def _summary(payload: dict) -> tuple[str, str]:
    inp = payload.get("tool_input", {}) or {}
    file_path = inp.get("file_path", "<unknown>")
    if "old_string" in inp:
        line_range = "edit"
    elif "content" in inp:
        lines = inp.get("content", "").count("\n") + 1
        line_range = f"1-{lines} (created)"
    else:
        line_range = "edit"
    return file_path, line_range


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    tool = payload.get("tool_name", "")
    if tool not in EDITING_TOOLS:
        return 0

    repo = Path.cwd()
    spec_id = _active_spec_id(repo)
    if spec_id is None:
        return 0

    file_path, line_range = _summary(payload)
    log_dir = repo / ".claude" / "decisions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{spec_id}.md"
    block = (
        f"## {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        f"- File: {file_path}\n"
        f"- Lines: {line_range}\n"
        f"- Summary: {tool} on {file_path}\n"
        f"- Tool: {tool}\n\n"
    )
    if not log_file.exists():
        header = f"# Decisions: {spec_id}\n\nAppend-only log of changes authorized by this spec.\n\n"
        log_file.write_text(header + block, encoding="utf-8")
    else:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Make it executable, run tests**

```bash
chmod +x hooks/post_tool_use.py
pytest tests/test_post_tool_use.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add hooks/post_tool_use.py tests/test_post_tool_use.py
git commit -m "feat: PostToolUse hook appends to decisions log"
```

### Task 6.3: `session_start.py`

**Files:**
- Create: `hooks/session_start.py`
- Create: `tests/test_session_start.py`

Behavior:
- Reads stdin (may be empty).
- Prints to stdout a banner: either "active spec: X" or a reminder of the four-section template.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session_start.py
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "session_start.py"


def _run(cwd: Path) -> str:
    proc = subprocess.run(
        ["python", str(HOOK)], input="", capture_output=True, text=True, cwd=cwd
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_no_active_prints_reminder(tmp_path: Path):
    out = _run(tmp_path)
    assert "spec-trace" in out.lower()
    assert "no active spec" in out.lower()


def test_active_prints_id(tmp_path: Path):
    (tmp_path / ".claude" / "specs").mkdir(parents=True)
    (tmp_path / ".claude" / "specs" / "active").write_text("2026-05-07_demo\n")
    out = _run(tmp_path)
    assert "2026-05-07_demo" in out
```

- [ ] **Step 2: Run, watch them fail**

Run: `pytest tests/test_session_start.py -v`

- [ ] **Step 3: Implement `hooks/session_start.py`**

```python
#!/usr/bin/env python3
"""spec-trace SessionStart hook."""
from __future__ import annotations

import sys
from pathlib import Path

REMINDER = (
    "spec-trace: no active spec. Run `/spec <slug>` to define what you're building.\n"
    "  Spec template sections: Assumptions, Scope, Non-goals, Success criteria.\n"
)


def main() -> int:
    repo = Path.cwd()
    marker = repo / ".claude" / "specs" / "active"
    if marker.exists() and marker.read_text(encoding="utf-8").strip():
        sys.stdout.write(f"spec-trace: active spec is {marker.read_text(encoding='utf-8').strip()}\n")
        return 0
    sys.stdout.write(REMINDER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Tests pass**

```bash
chmod +x hooks/session_start.py
pytest tests/test_session_start.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hooks/session_start.py tests/test_session_start.py
git commit -m "feat: SessionStart hook surfaces active spec"
```

### Task 6.4: `spec-trace init` installs hooks into `.claude/settings.json`

**Files:**
- Modify: `src/spec_trace/cli.py` — make `init` also write a `.claude/settings.json` snippet that wires the three hooks.
- Modify: `tests/test_cli.py`.

- [ ] **Step 1: Add a failing test**

```python
def test_init_writes_settings_with_hooks(runner: CliRunner, tmp_path: Path):
    runner.invoke(app, ["init", "--root", str(tmp_path)])
    settings = (tmp_path / ".claude" / "settings.json").read_text()
    assert "PreToolUse" in settings
    assert "PostToolUse" in settings
    assert "SessionStart" in settings
    assert "pre_tool_use.py" in settings
```

- [ ] **Step 2: Implement settings writer**

In `cli.py`, the `init` command should additionally copy or write a `settings.json` that points at the hooks directory. Since the hooks live inside this project, when the CLI is installed the user has to run `spec-trace init --hooks-dir /path/to/hooks`. Default to a path resolved off the package install (use `importlib.resources` once we ship them as package data — leave as a follow-up note).

For v1 simplicity: `init` writes a settings.json that uses `python -m spec_trace.hooks.pre_tool_use`, and we move the hooks under `src/spec_trace/hooks/` so they ship in the wheel. Update Phase 6 tasks 6.1-6.3 to put the hooks under `src/spec_trace/hooks/` instead of top-level `hooks/`.

> **Decision recorded here:** hooks live at `src/spec_trace/hooks/{pre_tool_use,post_tool_use,session_start}.py` and are invoked via `python -m spec_trace.hooks.<name>`. Update the test paths in Tasks 6.1–6.3 accordingly when executing.

- [ ] **Step 3: Tests pass, commit**

```bash
git commit -am "feat: init writes .claude/settings.json that wires hooks"
```

---

## Phase 7 — SKILL.md and slash commands

Goal: the published skill at `.claude/skills/spec-trace/` exposes four slash commands that delegate to the CLI.

### Task 7.1: SKILL.md

**Files:**
- Create: `.claude/skills/spec-trace/SKILL.md`

The frontmatter follows the standard skill format:

```yaml
---
name: spec-trace
description: Use when starting any non-trivial code change in this repo — refuses Edit/Write until a one-page spec is written; logs every accepted edit with a backlink. Activates on `/spec`, `/trace`, `/coverage`, `/spec-help`.
---
```

Body sections (each ~10–20 lines):
1. What this skill does (one paragraph).
2. The four slash commands and what they do.
3. The four-section spec template (verbatim).
4. The discipline: write the spec, type `ready`, then code.
5. Quick-fix mode: how and when.
6. Pinned hook contract version (the Claude Code hook API version this skill was tested against).

- [ ] **Step 1: Write SKILL.md.** Use the four-section template from the SPEC verbatim. Cap total length at 200 lines.

- [ ] **Step 2: Commit.**

```bash
git add .claude/skills/spec-trace/SKILL.md
git commit -m "feat: SKILL.md with four slash commands and template"
```

### Task 7.2: Slash command shims

**Files:**
- Create: `.claude/skills/spec-trace/scripts/new_spec.py`
- Create: `.claude/skills/spec-trace/scripts/activate_spec.py`
- Create: `.claude/skills/spec-trace/scripts/coverage.py`
- Create: `.claude/skills/spec-trace/scripts/trace.py`

Each shim is ~10 lines: parse args, shell out to `spec-trace <subcommand> ...`, stream output.

- [ ] **Step 1: Write the four shims and a test that each one calls `spec-trace` with the right argv.** Use `unittest.mock.patch` on `subprocess.run`.

- [ ] **Step 2: Commit.**

```bash
git add .claude/skills/spec-trace/scripts tests/test_skill_shims.py
git commit -m "feat: slash command shims delegate to CLI"
```

### Task 7.3: Templates

**Files:**
- Create: `.claude/skills/spec-trace/templates/spec.md.template`
- Create: `.claude/skills/spec-trace/templates/decision_entry.md.template`

The spec template is the SPEC's "Spec template" section verbatim. The decision entry template is the block from `decisions.py`.

- [ ] **Step 1: Write both templates, commit.**

---

## Phase 8 — Install scripts

Goal: one-liner install for macOS, Linux, WSL, and Windows.

### Task 8.1: `install.sh`

**Files:**
- Create: `install.sh`

Behavior:
1. Detect OS, abort if not macOS/Linux/WSL.
2. Verify `python3 --version` >= 3.10 and `pipx --version` exist; if not, instruct.
3. `pipx install spec-trace`.
4. Print next-step: `spec-trace init` inside a repo.

- [ ] **Step 1: Write `install.sh` (~40 lines).**
- [ ] **Step 2: Test on macOS** (manually, in a fresh shell).
- [ ] **Step 3: Test on Linux** (Docker container `python:3.11-slim`).
- [ ] **Step 4: Test on WSL** (any Ubuntu WSL).
- [ ] **Step 5: Commit.**

### Task 8.2: `install.ps1`

**Files:**
- Create: `install.ps1`

Mirrors `install.sh` for PowerShell.

- [ ] **Step 1: Write and test on Windows VM.** Commit.

### Task 8.3: Document the install one-liner in README later (Phase 11). Keep both scripts idempotent.

---

## Phase 9 — Eval suite

Goal: a reproducible three-arm benchmark with five fixtures. **This is the launch's hero.**

### Task 9.1: Fixture creation (5 tasks)

**Files:**
- Create: `evals/fixtures/task_001_add_auth/{starting_state.tar.gz, prompt.md, expected.md}`
- ... and four more.

Each fixture:
- `starting_state.tar.gz`: a small tarball of a working repo.
- `prompt.md`: the exact text the user types to Claude Code.
- `expected.md`: a reviewer's notes — what a correct change looks like.

The five tasks are listed in `SPEC_spec-trace.md` "Evaluation methodology". Use those.

- [ ] **Step 1: Curate task_001 (Flask + JWT auth).** Build the starting repo by hand. Verify the prompt produces a reasonable response in the control arm.
- [ ] **Step 2–5: Same for tasks 002–005.**
- [ ] **Step 6: Commit each fixture in its own commit.**

Time estimate: 3–4 hours total. The bottleneck for the whole project.

### Task 9.2: Eval runner (`evals/run_eval.py`)

For each (arm, task), the runner:
1. Extracts `starting_state.tar.gz` to a temp dir.
2. For arm B/C, places the skill + (for C) wires hooks.
3. Spawns `claude` in headless mode with the prompt:
   `claude -p --output-format=stream-json < prompt.md > session.jsonl`
4. Records: wall-clock, files modified, JSONL session log.

- [ ] **Step 1: Write the runner with `--arm A|B|C --task NN` and `--all`.**
- [ ] **Step 2: Smoke-test with `--task 001 --arm A`.**
- [ ] **Step 3: Commit.**

### Task 9.3: Measurement (`evals/measure.py`)

Parses `session.jsonl` per run and computes:
- Files modified outside scope (from the fixture's `expected.md` scope list).
- Number of clarifying interruptions (count messages where Claude asked a question instead of acting).
- Wall-clock from runner output.
- Test pass rate (by running the fixture's tests after Claude declares done).
- Token cost (sum from JSONL).
- Reviewer score: write `evals/review_template.md` for two human reviewers; `measure.py` reads two filled-in copies and averages.

- [ ] **Step 1: Implement, write tests against a fake JSONL.** Commit.

### Task 9.4: Initial published results

Run `make eval` end-to-end. Author `evals/results/2026-05-XX.md` with:
- Methodology (link to `evals/README.md`).
- Per-task per-arm scorecard.
- Headline number + caveat paragraph.
- A statement of limitations.

- [ ] **Step 1: Run, review, write up, commit.**

---

## Phase 10 — Examples and docs

These are launch-supporting artifacts. Each is small.

### Task 10.1: `examples/`

Three small reference projects with `.claude/` populated:
- `minimal-python-cli` (a 200-line Click app)
- `react-component` (a Vite + React component)
- `go-microservice` (a tiny chi-based HTTP service)

Each shows: a written spec, a decisions log, three commits with `Spec:` trailers.

- [ ] **Step 1: Build each, commit each as its own commit.**

### Task 10.2: `docs/`

Five markdown files, ~200–400 lines each:
- `PHILOSOPHY.md` — the four-section template; why discipline; why hooks not vibes.
- `ARCHITECTURE.md` — three pieces, the sync point, the hook lifecycle.
- `HOOKS.md` — exact JSON shapes, edge cases, hook contract version, troubleshooting.
- `TROUBLESHOOTING.md` — common errors and fixes.
- `COMPARISONS.md` — vs Karpathy CLAUDE.md, vs Cursor rules, vs MCP, vs Caveman.

- [ ] **Step 1: Draft each.** Run through the linter. Commit each separately.

---

## Phase 11 — README, GIF, release

This is the launch artifact. Last to land.

### Task 11.1: Record the terminal GIF

Use [terminalizer](https://github.com/faressoft/terminalizer) (cleaner output than asciicast for embedded use):

```bash
terminalizer record demo
# follow the SPEC's worked example: prompt -> spec -> diff -> decisions
terminalizer render demo -o demo.gif
```

- [ ] **Step 1: Record, edit, save under `docs/assets/demo.gif`.** Commit.

### Task 11.2: README

Use the SPEC's "README structure" section verbatim. Five things in this order: hero, problem, fix in 30 seconds, benchmark numbers, install + first spec.

Below the fold: architecture, comparisons, FAQ, contributing, license.

Banned: marketing tone, hype emoji (one rock 🪨 in the hero is the cap), promises about future versions.

- [ ] **Step 1: Draft, paste in benchmark numbers, link the GIF.** Commit.

### Task 11.3: Release workflow

**Files:**
- Create: `.github/workflows/release.yml`

Triggers on tag push (no `v` prefix). Builds wheel + sdist with `hatch build`, uploads to PyPI via `pypa/gh-action-pypi-publish`.

- [ ] **Step 1: Write workflow, set PyPI token in GitHub secrets, dry-run with a release candidate.** Commit.

### Task 11.4: Definition of done audit

Walk through every checkbox in `SPEC_spec-trace.md` "Definition of done for v1". Confirm each one. If anything fails, file the gap and fix.

- [ ] **Step 1: Audit, fix gaps, then ship.**

---

## Self-review against the SPEC

| SPEC requirement | Plan coverage |
| --- | --- |
| Four slash commands | Phase 7 |
| Two lifecycle hooks (Pre/Post) + SessionStart | Phase 6 |
| Python CLI with `init`, `new`, `activate`, `done`, `coverage`, `trace`, `status` | Phases 1–4 |
| Spec template (four sections) | Phase 1 (template constant), Phase 7 (file template) |
| Decision log format | Phase 2 + Phase 6 |
| `.claude/specs/active` sync point | Phase 1 |
| `prepare-commit-msg` for `Spec:` trailer | Phase 5 |
| Eval suite (3 arms × 5 fixtures, runner, measure, results) | Phase 9 |
| Install scripts (sh + ps1) | Phase 8 |
| Three example projects | Phase 10.1 |
| Docs (PHILOSOPHY, ARCHITECTURE, HOOKS, TROUBLESHOOTING, COMPARISONS) | Phase 10.2 |
| README + GIF | Phase 11 |
| CI green | Phase 0.3 |
| Release workflow on tag | Phase 11.3 |
| MIT LICENSE | Phase 0.1 |
| Quick-fix mode | Phase 6.1 (env var) |
| Hook contract version pinned | Phase 7.1 |
| Honest reporting in eval results | Phase 9.4 |

No SPEC requirement is uncovered.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-07-spec-trace-v1.md`. Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
