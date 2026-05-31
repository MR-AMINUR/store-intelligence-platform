.PHONY: help install test lint format typecheck clean run-api

help:
	@echo "Store Intelligence Platform - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run test suite with coverage"
	@echo "  make lint       - Run linter (flake8)"
	@echo "  make format     - Format code with black"
	@echo "  make typecheck  - Run type checker (mypy)"
	@echo "  make clean      - Remove generated files"
	@echo "  make run-api    - Start API server"
	@echo "  make all        - Run format, lint, typecheck, and test"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/ -v -m unit

test-property:
	pytest tests/ -v -m property

test-integration:
	pytest tests/ -v -m integration

lint:
	flake8 src/ tests/ --max-line-length=100 --exclude=venv,__pycache__

format:
	black src/ tests/ --line-length=100

format-check:
	black src/ tests/ --line-length=100 --check

typecheck:
	mypy src/

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

run-api:
	uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

all: format lint typecheck test

.DEFAULT_GOAL := help
