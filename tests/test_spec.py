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
