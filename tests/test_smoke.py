import re

from specwarden import __version__


def test_version_is_semver_shaped():
    assert isinstance(__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None


def test_version_sources_agree():
    """pyproject and __init__ both carry the version; drift ships a wrong number."""
    import re
    from pathlib import Path

    import tomllib

    import specwarden

    root = Path(__file__).resolve().parents[1]
    declared = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]

    assert specwarden.__version__ == declared
    assert re.fullmatch(r"\d+\.\d+\.\d+", declared)
