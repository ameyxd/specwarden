.PHONY: test lint fmt eval install-dev

install-dev:
	pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff check --fix .
	ruff format .

# Full sweep. --max-total-seconds keeps an unattended run bounded; individual
# cells are bounded by --cell-timeout (default 420s) inside the runner.
eval:
	python3 evals/run_eval.py --all-tasks --all-arms --max-total-seconds 3600

# Isolates the enforcement layer. Arm A has no hooks, arm D has hooks and no
# skill text. Arm C cannot be used for this: the skill sits in its system prompt,
# so the model predicts the block and never attempts an edit.
eval-enforcement:
	python3 evals/run_eval.py --all-tasks --arm A --out evals/results/_enf_A --max-total-seconds 1800
	python3 evals/run_eval.py --all-tasks --arm D --out evals/results/_enf_D --max-total-seconds 1800
