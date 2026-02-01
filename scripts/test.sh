#!/bin/bash
# ComplianceAgent - Test Runner Script

set -e

ROOT_DIR="$(dirname "$0")/.."

run_backend_tests() {
    echo "🐍 Running backend tests..."
    cd "$ROOT_DIR/backend"
    
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    
    pytest tests/ -v --cov=app --cov-report=term-missing "${@:2}"
}

run_frontend_tests() {
    echo "⚛️  Running frontend tests..."
    cd "$ROOT_DIR/frontend"
    npm test -- --coverage "${@:2}"
}

run_lint() {
    echo "🔍 Running linters..."
    
    echo "  Backend (ruff)..."
    cd "$ROOT_DIR/backend"
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    ruff check .
    ruff format --check .
    
    echo "  Frontend (eslint)..."
    cd "$ROOT_DIR/frontend"
    npm run lint
}

run_typecheck() {
    echo "📝 Running type checks..."
    
    echo "  Backend (mypy)..."
    cd "$ROOT_DIR/backend"
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    mypy app --ignore-missing-imports
    
    echo "  Frontend (tsc)..."
    cd "$ROOT_DIR/frontend"
    npm run type-check
}

case "$1" in
    "backend")
        run_backend_tests "$@"
        ;;
    "frontend")
        run_frontend_tests "$@"
        ;;
    "lint")
        run_lint
        ;;
    "typecheck")
        run_typecheck
        ;;
    "all")
        run_lint
        run_typecheck
        run_backend_tests
        run_frontend_tests
        ;;
    *)
        echo "Usage: $0 {backend|frontend|lint|typecheck|all}"
        echo ""
        echo "Commands:"
        echo "  backend   - Run Python tests with pytest"
        echo "  frontend  - Run JavaScript tests with Jest"
        echo "  lint      - Run linters (ruff + eslint)"
        echo "  typecheck - Run type checkers (mypy + tsc)"
        echo "  all       - Run everything"
        exit 1
        ;;
esac

echo "✅ Tests complete!"
