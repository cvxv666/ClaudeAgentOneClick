#!/usr/bin/env bash
# Vault git sync — runs via cron every 5 minutes.
# Pull remote -> commit local changes -> push.

set -euo pipefail

VAULT="${BRAIN_VAULT_PATH:-$HOME/vault}"
LOG="${BRAIN_DIR:-$(dirname "$0")/..}/logs/vault-sync.log"

mkdir -p "$(dirname "$LOG")"

cd "$VAULT"

ts=$(date '+%Y-%m-%d %H:%M:%S')

# 1. Pull remote changes
if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
    echo "$ts ERROR: pull failed" >> "$LOG"
    exit 1
fi

# 2. Check for local changes
if [ -z "$(git status --porcelain)" ]; then
    exit 0
fi

# 3. Stage + commit + push
changed=$(git status --porcelain | wc -l)
git add -A
git commit -m "vault: auto-sync $ts ($changed files)" --quiet
if git push --quiet 2>>"$LOG"; then
    echo "$ts OK: committed and pushed $changed files" >> "$LOG"
else
    echo "$ts ERROR: push failed" >> "$LOG"
    exit 1
fi
