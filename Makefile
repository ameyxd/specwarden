.PHONY: test lint fmt eval install-dev

install-dev:
	pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff format .
	ruff check --fix .

eval:
	python evals/run_eval.py
