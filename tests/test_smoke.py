import re

from spec_trace import __version__


def test_version_is_semver_shaped():
    assert isinstance(__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None
