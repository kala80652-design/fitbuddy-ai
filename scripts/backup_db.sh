#!/usr/bin/env bash
# ============================================================================
# FitBuddy SQLite Online Zero-Downtime Backup & Snapshot Script
# Target: /app/data/fitbuddy.db -> /app/data/backups/
# ============================================================================

set -eo pipefail

DB_PATH="${1:-/app/data/fitbuddy.db}"
BACKUP_DIR="${2:-/app/data/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/fitbuddy_backup_${TIMESTAMP}.sqlite"

mkdir -p "${BACKUP_DIR}"

if [ ! -f "${DB_PATH}" ]; then
    echo " Error: Database file ${DB_PATH} does not exist."
    exit 1
fi

echo " Starting online atomic snapshot of ${DB_PATH}..."
# Use SQLite's safe online backup API (.backup) to prevent write-lock corruption
sqlite3 "${DB_PATH}" ".backup '${BACKUP_FILE}'"

# Compress backup
gzip -9 "${BACKUP_FILE}"
echo " Backup created: ${BACKUP_FILE}.gz"

# Retention policy: Keep the last 7 daily snapshots, remove older
find "${BACKUP_DIR}" -type f -name "fitbuddy_backup_*.sqlite.gz" -mtime +7 -delete
echo " Retention policy executed. Expired backups pruned."
