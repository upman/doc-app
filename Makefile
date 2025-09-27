.PHONY: install run dev clean help setup test lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Create virtual environment and install dependencies"
	@echo "  install    - Install dependencies in existing virtual environment"
	@echo "  run        - Run the FastAPI server in production mode"
	@echo "  dev        - Run the FastAPI server in development mode with auto-reload"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting with ruff"
	@echo "  format     - Format code with black"
	@echo "  clean      - Clean up Python cache files and virtual environment"
	@echo "  help       - Show this help message"

# Create virtual environment and install dependencies
setup:
	cd backend && uv venv
	cd backend && uv pip install -e .
	cd backend && uv pip install -e .[dev]

# Install dependencies in existing virtual environment
install:
	cd backend && uv pip install -e .
	cd backend && uv pip install -e .[dev]

# Run server in production mode
run:
	cd backend && uv run uvicorn doc_app_backend.main:app --host 0.0.0.0 --port 8000

# Run server in development mode with auto-reload
dev:
	cd backend && uv run uvicorn doc_app_backend.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	cd backend && uv run pytest

# Run linting
lint:
	cd backend && uv run ruff check .

# Format code
format:
	cd backend && uv run black .
	cd backend && uv run ruff check --fix .

# Clean Python cache files and virtual environment
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf backend/.venv