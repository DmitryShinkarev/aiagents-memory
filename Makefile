.PHONY: help install dev-install test lint format clean docker-up docker-down init

help:
	@echo "Memory-Agents Makefile Commands:"
	@echo "  install       - Install production dependencies"
	@echo "  dev-install   - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linters"
	@echo "  format        - Format code"
	@echo "  clean         - Clean temporary files"
	@echo "  docker-up     - Start Docker services"
	@echo "  docker-down   - Stop Docker services"
	@echo "  init          - Initialize databases"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=memory_agents --cov-report=html

lint:
	ruff check .
	mypy memory_agents/

format:
	black .
	ruff check --fix .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov dist build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

init:
	@echo "Initializing databases..."
	@echo "MongoDB and PostgreSQL will initialize automatically via Docker"
	@echo "Run 'make docker-up' to start services"

run-example:
	python examples/basic_usage.py





