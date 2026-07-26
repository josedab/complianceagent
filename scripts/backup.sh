#!/usr/bin/env bash
# ComplianceAgent — Production Database Backup Script
# Creates an encrypted, checksummed PostgreSQL backup and optionally uploads to S3.
#
# Usage:
#   ./scripts/backup.sh                      # interactive, uses .env defaults
#   ./scripts/backup.sh --yes --upload-s3    # non-interactive, upload to S3
#
# Environment variables (or .env):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
#   BACKUP_ENCRYPTION_KEY  — passphrase for AES-256 encryption (REQUIRED)
#   BACKUP_S3_BUCKET       — S3 bucket for remote storage (optional)
#   BACKUP_RETENTION_DAYS  — local retention in days (default: 30)

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
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DB_HOST="${POSTGRES_HOST:?POSTGRES_HOST is required}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:?POSTGRES_USER is required}"
DB_NAME="${POSTGRES_DB:?POSTGRES_DB is required}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required}"
S3_BUCKET="${BACKUP_S3_BUCKET:-}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
AUTO_CONFIRM="${1:-}"
UPLOAD_S3=false

# ── Parse args ──
for arg in "$@"; do
    case "$arg" in
        --yes|-y) AUTO_CONFIRM="--yes" ;;
        --upload-s3) UPLOAD_S3=true ;;
        --help|-h)
            echo "Usage: $0 [--yes] [--upload-s3]"
            echo "  --yes         Skip confirmation prompt"
            echo "  --upload-s3   Upload backup to S3_BUCKET after creation"
            exit 0
            ;;
    esac
done

# ── Safety confirmation ──
echo "╔══════════════════════════════════════════════════╗"
echo "║  ComplianceAgent — Production Database Backup    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Host:      $DB_HOST:$DB_PORT"
echo "  Database:  $DB_NAME"
echo "  User:      $DB_USER"
echo "  Output:    $BACKUP_DIR/"
echo "  Retention: $RETENTION_DAYS days"
echo "  Upload S3: $UPLOAD_S3"
echo ""

if [ "$AUTO_CONFIRM" != "--yes" ]; then
    read -rp "Proceed with backup? [y/N] " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# ── Create backup directory ──
mkdir -p "$BACKUP_DIR"

DUMP_FILE="$BACKUP_DIR/complianceagent_${TIMESTAMP}.sql.gz"
ENC_FILE="${DUMP_FILE}.enc"
CHECKSUM_FILE="${ENC_FILE}.sha256"

# ── Dump + compress ──
echo "→ Creating database dump..."
export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    --verbose 2>/dev/null \
    | gzip > "$DUMP_FILE"
unset PGPASSWORD

DUMP_SIZE=$(du -sh "$DUMP_FILE" | cut -f1)
echo "  ✓ Dump created: $DUMP_FILE ($DUMP_SIZE)"

# ── Encrypt ──
echo "→ Encrypting backup..."
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 \
    -in "$DUMP_FILE" \
    -out "$ENC_FILE" \
    -pass "pass:$ENCRYPTION_KEY"

# Remove unencrypted dump
rm -f "$DUMP_FILE"
echo "  ✓ Encrypted: $ENC_FILE"

# ── Checksum ──
echo "→ Computing checksum..."
shasum -a 256 "$ENC_FILE" > "$CHECKSUM_FILE"
echo "  ✓ Checksum: $(cat "$CHECKSUM_FILE")"

# ── Upload to S3 ──
if [ "$UPLOAD_S3" = true ] && [ -n "$S3_BUCKET" ]; then
    echo "→ Uploading to s3://$S3_BUCKET/backups/..."
    aws s3 cp "$ENC_FILE" "s3://$S3_BUCKET/backups/$(basename "$ENC_FILE")" --sse aws:kms
    aws s3 cp "$CHECKSUM_FILE" "s3://$S3_BUCKET/backups/$(basename "$CHECKSUM_FILE")" --sse aws:kms
    echo "  ✓ Uploaded to S3"
fi

# ── Retention cleanup ──
echo "→ Cleaning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "complianceagent_*.enc" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "complianceagent_*.sha256" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
echo "  ✓ Retention policy applied"

echo ""
echo "✅ Backup complete: $ENC_FILE"
echo "   Checksum:        $CHECKSUM_FILE"
echo ""
echo "📋 Retention guidance:"
echo "   • Keep daily backups for $RETENTION_DAYS days"
echo "   • Keep weekly backups for 90 days"
echo "   • Keep monthly backups for 1 year"
echo "   • Test restore quarterly (make restore-test)"
