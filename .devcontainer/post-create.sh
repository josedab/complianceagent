#!/bin/bash
# Post-create script for dev container setup
set -e

echo "🚀 Setting up ComplianceAgent development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd /workspace/backend
pip install uv
uv venv
uv pip install -e ".[dev]"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd /workspace/frontend
npm install

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
cd /workspace
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg

# Install Playwright browsers (for regulatory crawling)
echo "🎭 Installing Playwright browsers..."
cd /workspace/backend
source .venv/bin/activate
playwright install chromium
playwright install-deps chromium

# Wait for database to be ready
echo "⏳ Waiting for database..."
until pg_isready -h postgres -p 5432 -U postgres; do
  sleep 1
done

# Run database migrations
echo "🗃️ Running database migrations..."
cd /workspace/backend
source .venv/bin/activate
alembic upgrade head

echo "✅ Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  make run-backend   - Start the FastAPI backend"
echo "  make run-frontend  - Start the Next.js frontend"
echo "  make run-workers   - Start Celery workers"
echo "  make test          - Run all tests"
echo "  make lint          - Run linters"
echo ""
