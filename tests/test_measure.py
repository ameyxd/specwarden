import json
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"
sys.path.insert(0, str(EVALS_DIR))
from measure import measure, parse_jsonl, render_scorecard  # noqa: E402


def test_parse_jsonl_counts_questions(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {"type": "assistant", "message": {"content": [{"text": "Done."}]}},
        {"type": "assistant", "message": {"content": [{"text": "Should I also rename the file?"}]}},
        {"type": "assistant", "message": {"content": [{"text": "Working on it"}]}},
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    clarifications, tokens = parse_jsonl(log)

    assert clarifications == 1
    assert tokens == 0


def test_parse_jsonl_sums_tokens(tmp_path: Path):
    log = tmp_path / "session.jsonl"
    events = [
        {
            "type": "assistant",
            "message": {"content": [], "usage": {"input_tokens": 100, "output_tokens": 50}},
        },
        {
            "type": "assistant",
            "message": {"content": [], "usage": {"input_tokens": 30, "output_tokens": 10}},
        },
    ]
    log.write_text("\n".join(json.dumps(e) for e in events))

    _, tokens = parse_jsonl(log)

    assert tokens == 190


def test_measure_assembles_summary(tmp_path: Path):
    log = tmp_path / "task_001_A_111.jsonl"
    log.write_text(
        json.dumps({"type": "assistant", "message": {"content": [{"text": "Done."}]}}) + "\n"
    )

    summary = [
        {
            "task": "task_001_demo",
            "arm": "A",
            "wall_seconds": 12.5,
            "files_modified": 3,
            "exit_status": 0,
            "log_path": log.name,
        }
    ]
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    # measure() resolves log_path relative to results_dir.parent.parent — so we set up the
    # caller's expectation: results_dir is `tmp_path`, parent.parent is two above. Use a
    # nested layout to match.
    nested = tmp_path / "evals" / "results" / "_local"
    nested.mkdir(parents=True)
    (nested / "summary.json").write_text(
        json.dumps(
            [
                {
                    "task": "task_001_demo",
                    "arm": "A",
                    "wall_seconds": 12.5,
                    "files_modified": 3,
                    "exit_status": 0,
                    "log_path": f"evals/results/_local/{log.name}",
                }
            ]
        )
    )
    (nested / log.name).write_text(
        json.dumps({"type": "assistant", "message": {"content": [{"text": "Done."}]}}) + "\n"
    )

    measurements = measure(nested)

    assert len(measurements) == 1
    assert measurements[0].task == "task_001_demo"
    assert measurements[0].arm == "A"
    assert measurements[0].wall_seconds == 12.5


def test_render_scorecard_table_shape():
    from measure import Measurement

    rows = [Measurement("task_001_demo", "A", 10.0, 2, 0, 1234, 0)]
    table = render_scorecard(rows)
    assert "| Task | Arm | Wall (s) | Files mod. | Clarifications | Tokens | Exit |" in table
    assert "task_001_demo" in table
