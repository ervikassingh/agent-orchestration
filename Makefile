.PHONY: install lint test build clean run-web run-api

install:
	poetry install
	cd web-ui && npm install

lint:
	poetry run ruff check .
	poetry run mypy packages/

test:
	poetry run pytest

build:
	poetry build
	cd web-ui && npm run build

run-api:
	poetry run uvicorn api_server.main:app --reload --port 8000

run-web:
	cd web-ui && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf web-ui/node_modules/ web-ui/dist/

precommit: lint test