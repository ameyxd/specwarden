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
