#!/bin/bash
# ComplianceAgent - Database Migration Script

set -e

cd "$(dirname "$0")/../backend"

# Activate virtual environment if exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

case "$1" in
    "upgrade")
        echo "⬆️  Upgrading database to latest..."
        alembic upgrade head
        ;;
    "downgrade")
        echo "⬇️  Downgrading database..."
        alembic downgrade -1
        ;;
    "revision")
        if [ -z "$2" ]; then
            echo "Usage: $0 revision <message>"
            exit 1
        fi
        echo "📝 Creating new migration: $2"
        alembic revision --autogenerate -m "$2"
        ;;
    "history")
        echo "📜 Migration history:"
        alembic history
        ;;
    "current")
        echo "📍 Current revision:"
        alembic current
        ;;
    *)
        echo "Usage: $0 {upgrade|downgrade|revision <message>|history|current}"
        exit 1
        ;;
esac

echo "✅ Done!"
