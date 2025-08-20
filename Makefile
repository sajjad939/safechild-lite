# SafeChild-Lite Makefile
# Convenient commands for development and deployment

.PHONY: help install setup start start-backend start-frontend test clean lint format docs

# Default target
help:
	@echo "SafeChild-Lite Development Commands"
	@echo "=================================="
	@echo "install     - Install dependencies"
	@echo "setup       - Run complete setup"
	@echo "start       - Start both backend and frontend"
	@echo "start-backend - Start only backend service"
	@echo "start-frontend - Start only frontend service"
	@echo "test        - Run all tests"
	@echo "test-backend - Run backend tests only"
	@echo "test-frontend - Run frontend tests only"
	@echo "clean       - Clean temporary files"
	@echo "lint        - Run code linting"
	@echo "format      - Format code"
	@echo "docs        - Generate documentation"
	@echo "health      - Check system health"

# Installation and setup
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

setup:
	@echo "🔧 Running setup..."
	python setup.py

# Start services
start:
	@echo "🚀 Starting SafeChild-Lite..."
	python start.py

start-backend:
	@echo "🚀 Starting backend service..."
	python run_backend.py

start-frontend:
	@echo "🚀 Starting frontend service..."
	python run_frontend.py

# Testing
test:
	@echo "🧪 Running all tests..."
	pytest tests/ -v

test-backend:
	@echo "🧪 Running backend tests..."
	pytest tests/test_*.py -v

test-frontend:
	@echo "🧪 Running frontend tests..."
	pytest tests/frontend/ -v

# Code quality
lint:
	@echo "🔍 Running linting..."
	flake8 backend/ frontend/ --max-line-length=120
	pylint backend/ frontend/ --disable=C0114,C0115,C0116

format:
	@echo "✨ Formatting code..."
	black backend/ frontend/ --line-length=120
	isort backend/ frontend/

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "API docs available at: http://localhost:8000/docs"

# Maintenance
clean:
	@echo "🧹 Cleaning temporary files..."
	rm -rf temp/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

health:
	@echo "🏥 Checking system health..."
	python -c "import requests; print('✅ Backend:', 'OK' if requests.get('http://localhost:8000/health', timeout=5).status_code == 200 else 'FAIL')\" 2>/dev/null || echo "❌ Backend: Not running"
	python -c "import requests; print('✅ Frontend:', 'OK' if requests.get('http://localhost:8501', timeout=5).status_code == 200 else 'FAIL')\" 2>/dev/null || echo "❌ Frontend: Not running"

# Development helpers
dev-install:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install black flake8 pylint isort pytest-cov

dev-setup: dev-install setup
	@echo "🔧 Development environment ready!"

# Docker commands
docker-build:
	@echo "🐳 Building Docker images..."
	docker-compose build

docker-start:
	@echo "🐳 Starting Docker containers..."
	docker-compose up -d

docker-stop:
	@echo "🐳 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Production commands
prod-install:
	@echo "📦 Installing production dependencies..."
	pip install -r requirements.txt --no-dev

prod-start:
	@echo "🚀 Starting production services..."
	APP_ENV=production python start.py

# Backup and restore
backup:
	@echo "💾 Creating backup..."
	tar -czf safechild-backup-$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=temp/ \
		--exclude=__pycache__/ \
		--exclude=.git/ \
		.

# Version and release
version:
	@echo "📋 SafeChild-Lite v1.0.0"
	@echo "Python: $(shell python --version)"
	@echo "Platform: $(shell python -c 'import platform; print(platform.system())')"

# Help for specific commands
help-install:
	@echo "Install command: Downloads and installs all required Python packages"

help-setup:
	@echo "Setup command: Runs complete application setup including directory creation and config files"

help-start:
	@echo "Start command: Launches both backend (FastAPI) and frontend (Streamlit) services"

help-test:
	@echo "Test command: Runs the complete test suite using pytest"