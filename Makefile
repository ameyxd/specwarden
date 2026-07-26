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

eval:
	python3 evals/run_eval.py --all-tasks --all-arms

eval-enforcement:
	python3 evals/run_eval.py --all-tasks --arm B --adversarial --out evals/results/_adv_B
	python3 evals/run_eval.py --all-tasks --arm C --adversarial --out evals/results/_adv_C
