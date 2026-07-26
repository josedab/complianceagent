#!/usr/bin/env bash
# ComplianceAgent — Production Database Restore Script
# Restores a database from an encrypted backup created by backup.sh.
#
# Usage:
#   ./scripts/restore.sh <backup-file.sql.gz.enc>
#   ./scripts/restore.sh --from-s3 <s3-key>
#
# Environment variables (or .env):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
#   BACKUP_ENCRYPTION_KEY  — must match the key used during backup
#   BACKUP_S3_BUCKET       — S3 bucket (required with --from-s3)
#
# ⚠ WARNING: This will DROP and recreate the target database.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env"
    set +a
fi

# ── Config ──
DB_HOST="${POSTGRES_HOST:?POSTGRES_HOST is required}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:?POSTGRES_USER is required}"
DB_NAME="${POSTGRES_DB:?POSTGRES_DB is required}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
FROM_S3=false
BACKUP_FILE=""

# ── Parse args ──
while [ $# -gt 0 ]; do
    case "$1" in
        --from-s3) FROM_S3=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--from-s3] <backup-file-or-s3-key>"
            echo "  --from-s3   Download backup from S3 before restoring"
            exit 0
            ;;
        *) BACKUP_FILE="$1"; shift ;;
    esac
done

if [ -z "$BACKUP_FILE" ]; then
    echo "Error: Backup file path is required"
    echo "Usage: $0 [--from-s3] <backup-file.sql.gz.enc>"
    exit 1
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║  ComplianceAgent — Production Database Restore   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Host:     $DB_HOST:$DB_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo "  Source:   $BACKUP_FILE"
echo ""
echo "  ⚠  THIS WILL DESTROY ALL DATA IN '$DB_NAME'"
echo ""

# ── Double confirmation for production ──
read -rp "Type the database name to confirm: " confirm_db
if [ "$confirm_db" != "$DB_NAME" ]; then
    echo "Database name does not match. Aborted."
    exit 1
fi

read -rp "Type 'RESTORE' to proceed: " confirm_action
if [ "$confirm_action" != "RESTORE" ]; then
    echo "Aborted."
    exit 1
fi

# ── Download from S3 if needed ──
if [ "$FROM_S3" = true ]; then
    if [ -z "$S3_BUCKET" ]; then
        echo "Error: BACKUP_S3_BUCKET is required with --from-s3"
        exit 1
    fi
    LOCAL_FILE="/tmp/$(basename "$BACKUP_FILE")"
    echo "→ Downloading from s3://$S3_BUCKET/backups/$BACKUP_FILE..."
    aws s3 cp "s3://$S3_BUCKET/backups/$BACKUP_FILE" "$LOCAL_FILE"
    
    # Download and verify checksum
    CHECKSUM_KEY="${BACKUP_FILE}.sha256"
    aws s3 cp "s3://$S3_BUCKET/backups/$CHECKSUM_KEY" "${LOCAL_FILE}.sha256" 2>/dev/null || true
    BACKUP_FILE="$LOCAL_FILE"
    echo "  ✓ Downloaded"
fi

# ── Verify file exists ──
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# ── Verify checksum ──
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    echo "→ Verifying checksum..."
    if shasum -a 256 -c "$CHECKSUM_FILE" --status 2>/dev/null; then
        echo "  ✓ Checksum verified"
    else
        echo "  ✗ CHECKSUM MISMATCH — backup may be corrupted"
        read -rp "Continue anyway? [y/N] " force
        if [ "$force" != "y" ]; then
            echo "Aborted."
            exit 1
        fi
    fi
else
    echo "  ⚠ No checksum file found — skipping verification"
fi

# ── Decrypt ──
echo "→ Decrypting backup..."
DECRYPTED_FILE="/tmp/complianceagent_restore_$$.sql.gz"
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 \
    -in "$BACKUP_FILE" \
    -out "$DECRYPTED_FILE" \
    -pass "pass:$ENCRYPTION_KEY"
echo "  ✓ Decrypted"

# ── Decompress ──
echo "→ Decompressing..."
UNCOMPRESSED_FILE="/tmp/complianceagent_restore_$$.sql"
gunzip -c "$DECRYPTED_FILE" > "$UNCOMPRESSED_FILE"
rm -f "$DECRYPTED_FILE"
echo "  ✓ Decompressed ($(du -sh "$UNCOMPRESSED_FILE" | cut -f1))"

# ── Restore ──
echo "→ Restoring database..."
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"

# Drop and recreate the database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\";"

# Restore the dump
pg_restore \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    --verbose \
    "$UNCOMPRESSED_FILE" 2>/dev/null || \
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$UNCOMPRESSED_FILE" 2>/dev/null

unset PGPASSWORD

# Cleanup temp files
rm -f "$UNCOMPRESSED_FILE"

echo ""
echo "✅ Database restored successfully from: $(basename "$BACKUP_FILE")"
echo ""
echo "📋 Post-restore steps:"
echo "   1. Verify data: psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c 'SELECT count(*) FROM alembic_version;'"
echo "   2. Run pending migrations: make migrate"
echo "   3. Verify application health: curl https://your-domain/health"
