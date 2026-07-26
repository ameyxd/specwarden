import re

from specwarden import __version__


def test_version_is_semver_shaped():
    assert isinstance(__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None


def test_version_sources_agree():
    """pyproject and __init__ both carry the version; drift ships a wrong number.

    Parsed with a regex rather than tomllib: tomllib is stdlib only from 3.11
    and this package supports 3.10, which CI tests.
    """
    import re
    from pathlib import Path

    import specwarden

    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)

    assert match is not None, "no version found in pyproject.toml"
    assert specwarden.__version__ == match.group(1)
    assert re.fullmatch(r"\d+\.\d+\.\d+", match.group(1))
