import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

SHIM_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "specwarden" / "scripts"


def _load(name: str):
    """Load a shim by inserting its directory on sys.path."""
    sys.path.insert(0, str(SHIM_DIR))
    try:
        if name in sys.modules:
            del sys.modules[name]
        return import_module(name)
    finally:
        sys.path.pop(0)


@patch("subprocess.call", return_value=0)
def test_new_spec_shim_calls_cli(mock_call):
    mod = _load("new_spec")
    assert mod.main(["Add", "JWT", "Auth"]) == 0
    mock_call.assert_called_once_with(["specwarden", "new", "Add JWT Auth", "--author", "claude"])


@patch("subprocess.call", return_value=0)
def test_activate_spec_shim_calls_cli(mock_call):
    mod = _load("activate_spec")
    assert mod.main(["2026-05-07_demo"]) == 0
    mock_call.assert_called_once_with(["specwarden", "activate", "2026-05-07_demo"])


@patch("subprocess.call", return_value=0)
def test_coverage_shim_passes_args(mock_call):
    mod = _load("coverage")
    assert mod.main(["--last", "10"]) == 0
    mock_call.assert_called_once_with(["specwarden", "coverage", "--last", "10"])


@patch("subprocess.call", return_value=0)
def test_trace_shim_defaults_to_head(mock_call):
    mod = _load("trace")
    assert mod.main([]) == 0
    mock_call.assert_called_once_with(["specwarden", "trace", "HEAD"])


def test_new_spec_shim_rejects_empty_argv():
    mod = _load("new_spec")
    assert mod.main([]) == 2
