.PHONY: help install dev web-dev web-build lint format test eval docker-build docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Start development server"
	@echo "  make web-dev       Start Next.js chat frontend"
	@echo "  make web-build     Build Next.js chat frontend"
	@echo "  make lint          Run code linter (ruff)"
	@echo "  make format        Auto-format code (ruff)"
	@echo "  make test          Run pytest suite"
	@echo "  make eval          Run agent evaluation scripts"
	@echo "  make docker-build  Build Docker container"
	@echo "  make docker-up     Start docker compose services"
	@echo "  make docker-down   Stop docker compose services"
	@echo "  make clean         Remove cache and temporary files"

install:
	pip install -r requirements.txt

dev:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest tests/

eval:
	python -m eval.scripts.run_eval

docker-build:
	docker build -t agentic-rag-legal-qa-hanoi:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
