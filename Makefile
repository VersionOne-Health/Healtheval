.PHONY: install install-dev test lint format clean build typecheck run-example

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/test_loader.py tests/test_deterministic.py tests/test_runner.py -v --tb=short

test-cov:
	pytest tests/ -v --cov=healtheval --cov-report=term-missing --cov-report=html

lint:
	ruff check healtheval/ tests/
	mypy healtheval/ --ignore-missing-imports

format:
	black healtheval/ tests/ examples/
	ruff check healtheval/ tests/ --fix

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

build:
	python -m build

typecheck:
	mypy healtheval/ --ignore-missing-imports

run-example:
	python examples/quickstart.py

smoke:
	healtheval list
	healtheval show SCRIBE-001
	healtheval run --failure-mode SCRIBE-001 \
		--context "Metformin was discontinued on 2024-11-14." \
		--agent-output "Patient is currently on metformin 500mg twice daily." \
		--no-llm

ci: install-dev test smoke
