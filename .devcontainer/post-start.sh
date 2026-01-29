#!/bin/bash
# Post-start script for dev container
set -e

echo "🔄 Starting development services..."

# Ensure services are running
cd /workspace

# Activate Python virtual environment for shell sessions
echo 'source /workspace/backend/.venv/bin/activate' >> ~/.bashrc

echo "✅ Ready for development!"
echo ""
echo "Quick start:"
echo "  Terminal 1: make run-backend"
echo "  Terminal 2: make run-frontend"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
