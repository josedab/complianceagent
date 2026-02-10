#!/bin/bash
# ComplianceAgent - Development Setup Script

set -e

echo "🚀 Setting up ComplianceAgent development environment..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }

# Verify Python 3.12+
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_MINOR" -lt 12 ]; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "❌ Python 3.12+ is required. Found: Python $PYTHON_VERSION"
    echo "   Install with: pyenv install 3.12 && pyenv local 3.12"
    exit 1
fi
echo "✅ Python $(python3 --version) detected"

# Verify Node.js 20+
NODE_MAJOR=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 20 ]; then
    echo "❌ Node.js 20+ is required. Found: $(node -v)"
    echo "   Install with: nvm install 20"
    exit 1
fi
echo "✅ Node.js $(node -v) detected"

# Create environment files if they don't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
fi

if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env..."
    cp backend/.env.example backend/.env
fi

# Start infrastructure
echo "🐳 Starting Docker infrastructure..."
cd docker
docker compose up -d postgres redis elasticsearch minio
cd ..

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend

if command -v uv >/dev/null 2>&1; then
    uv venv
    uv pip install -e ".[dev]"
else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
fi

# Run migrations
echo "📊 Running database migrations..."
source .venv/bin/activate 2>/dev/null || true
alembic upgrade head

cd ..

# Setup frontend
echo "⚛️  Setting up React frontend..."
cd frontend
npm install
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To seed demo data:"
echo "  make seed"
echo ""
echo "To start development:"
echo "  Backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo "  Workers:  cd backend && celery -A app.workers worker --loglevel=info"
echo ""
echo "Or run everything with Docker:"
echo "  cd docker && docker compose up"
echo ""
echo "Access:"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/api/docs"
