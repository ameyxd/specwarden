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


def test_active_spec_id_returns_none_for_blank_file(tmp_path: Path):
    p = RepoPaths(tmp_path)
    p.ensure_dirs()
    p.active_marker.write_text("   \n", encoding="utf-8")
    assert p.active_spec_id() is None
