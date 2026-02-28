#!/usr/bin/env bash
# Server backup script — encrypt + upload (customize upload target).
#
# Usage: ./backup.sh
# Cron: 0 4 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
#
# Prerequisites:
#   - GPG installed
#   - Passphrase file at ~/.backup-passphrase (chmod 600)
#   - Customize UPLOAD_CMD for your storage (S3, rclone, scp, etc.)

set -euo pipefail

HOME_DIR="${HOME:-/root}"
BACKUP_DIR="/tmp/server-backup"
DATE=$(date +%Y-%m-%d)
ARCHIVE_NAME="backup-${DATE}.tar.gz"
ENCRYPTED_NAME="${ARCHIVE_NAME}.gpg"
PASSPHRASE_FILE="${HOME_DIR}/.backup-passphrase"

log() { echo "[backup] $(date '+%H:%M:%S') $*"; }

# Check passphrase exists
if [ ! -f "$PASSPHRASE_FILE" ]; then
    echo "ERROR: Backup passphrase not found at $PASSPHRASE_FILE"
    echo "Create it: echo 'your-strong-passphrase' > $PASSPHRASE_FILE && chmod 600 $PASSPHRASE_FILE"
    exit 1
fi

# Clean up
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

log "Starting backup..."

# Save PM2 config
pm2 save --force 2>/dev/null || true

# Dump crontab
crontab -l > "$BACKUP_DIR/crontab.txt" 2>/dev/null || echo "# no crontab" > "$BACKUP_DIR/crontab.txt"

# Create the tarball — CUSTOMIZE these paths for your setup
log "Creating archive..."
cd "$HOME_DIR"

tar czf "$BACKUP_DIR/$ARCHIVE_NAME" \
    --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='.cache' \
    --exclude='.vscode-server' \
    --exclude='*.pyc' \
    --warning=no-file-changed \
    brain/src/ brain/scripts/ brain/pyproject.toml \
    vault/ \
    .claude/settings.json \
    .claude/skills/ \
    .claude/projects/-root/memory/ \
    .pm2/dump.pm2.json \
    .mcp.json \
    .takopi/ \
    CLAUDE.md \
    scripts/ \
    2>/dev/null || true

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR/$ARCHIVE_NAME" | cut -f1)
log "Archive created: $ARCHIVE_SIZE"

# Encrypt with GPG
log "Encrypting..."
gpg --batch --yes --symmetric --cipher-algo AES256 \
    --passphrase-file "$PASSPHRASE_FILE" \
    -o "$BACKUP_DIR/$ENCRYPTED_NAME" \
    "$BACKUP_DIR/$ARCHIVE_NAME"

rm "$BACKUP_DIR/$ARCHIVE_NAME"
ENCRYPTED_SIZE=$(du -h "$BACKUP_DIR/$ENCRYPTED_NAME" | cut -f1)
log "Encrypted: $ENCRYPTED_SIZE"

# Upload — CUSTOMIZE this for your storage
# Examples:
#   scp "$BACKUP_DIR/$ENCRYPTED_NAME" user@backup-server:/backups/
#   aws s3 cp "$BACKUP_DIR/$ENCRYPTED_NAME" s3://my-backups/
#   rclone copy "$BACKUP_DIR/$ENCRYPTED_NAME" remote:backups/
log "Upload step — customize UPLOAD_CMD in this script"
# UPLOAD_CMD "$BACKUP_DIR/$ENCRYPTED_NAME"

# Cleanup
rm -rf "$BACKUP_DIR"

log "Backup complete: $ENCRYPTED_NAME ($ENCRYPTED_SIZE)"
