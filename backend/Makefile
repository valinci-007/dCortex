PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup db validate test lint serve eval clean

## Create a virtualenv and install the package (editable) with dev + agent + llm + api extras
setup:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev,agent,llm,api,voice]"

## Rebuild the SQLite database from data/*.json
db:
	$(BIN)/crew-ops build-db --force

## Run the organiser-provided dataset validator against data/
validate:
	$(PY) scripts/validate_dataset.py data

## Run the test suite
test:
	$(BIN)/pytest -p no:warnings

## Lint (ruff)
lint:
	$(BIN)/ruff check src tests

## Run the local API on http://127.0.0.1:8000 (serves ../frontend/dist when built)
serve:
	$(BIN)/crew-ops serve

## Grade all tiers against the answer keys with the configured provider
eval:
	$(BIN)/crew-ops eval --tier 1 2 3

clean:
	rm -rf var/*.db .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
