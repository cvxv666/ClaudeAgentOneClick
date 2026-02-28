#!/usr/bin/env bash
# Claude Server Kit — automated setup script.
#
# What it does:
#   1. Installs uv (Python package manager)
#   2. Installs Node.js + PM2 (process manager)
#   3. Installs system dependencies (ffmpeg, pdftotext)
#   4. Sets up Brain MCP server
#   5. Installs Takopi (Telegram bot bridge)
#   6. Creates vault directory structure
#   7. Configures Claude Code (MCP, settings, CLAUDE.md)
#   8. Sets up cron jobs (vault sync, backup)
#   9. Downloads ML models
#
# Usage: bash setup.sh
#
# Run from the cloned repo directory.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="${HOME:-/root}"
VAULT_DIR="${HOME_DIR}/vault"
BRAIN_DIR="${HOME_DIR}/brain"
CLAUDE_DIR="${HOME_DIR}/.claude"
UV_BIN="${HOME_DIR}/.local/bin/uv"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*"; }

# ─────────────────────────────────────────────────
# 1. Install uv
# ─────────────────────────────────────────────────
log "Installing uv (Python package manager)..."
if command -v uv &>/dev/null; then
    log "uv already installed: $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME_DIR}/.local/bin:$PATH"
    log "uv installed: $(uv --version)"
fi

# Install Python 3.12
log "Installing Python 3.12..."
uv python install 3.12

# ─────────────────────────────────────────────────
# 2. Install Node.js + PM2
# ─────────────────────────────────────────────────
log "Installing Node.js + PM2..."
if command -v node &>/dev/null; then
    log "Node.js already installed: $(node --version)"
else
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    log "Node.js installed: $(node --version)"
fi

if command -v pm2 &>/dev/null; then
    log "PM2 already installed"
else
    npm install -g pm2
    pm2 startup systemd -u root --hp "$HOME_DIR" 2>/dev/null || true
    log "PM2 installed and configured"
fi

# ─────────────────────────────────────────────────
# 3. System dependencies
# ─────────────────────────────────────────────────
log "Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq ffmpeg poppler-utils git gpg curl jq

# ─────────────────────────────────────────────────
# 4. Set up Brain MCP server
# ─────────────────────────────────────────────────
log "Setting up Brain MCP server..."
if [ -d "$BRAIN_DIR" ]; then
    warn "Brain directory already exists at $BRAIN_DIR — skipping copy"
else
    cp -r "$REPO_DIR/brain" "$BRAIN_DIR"
    log "Brain copied to $BRAIN_DIR"
fi

# Install Python dependencies
cd "$BRAIN_DIR"
uv sync
log "Brain dependencies installed"

# ─────────────────────────────────────────────────
# 5. Install Takopi
# ─────────────────────────────────────────────────
log "Installing Takopi (Telegram bot bridge)..."
if command -v takopi &>/dev/null; then
    log "Takopi already installed"
else
    # Takopi requires Python 3.14+
    uv python install 3.14
    uv tool install -U takopi
    log "Takopi installed"
fi

echo ""
warn "Takopi needs configuration. Run: takopi"
warn "It will guide you through setup (bot token, chat ID, etc.)"
echo ""

# ─────────────────────────────────────────────────
# 6. Create vault structure
# ─────────────────────────────────────────────────
log "Creating vault structure..."
if [ -d "$VAULT_DIR" ]; then
    warn "Vault directory already exists at $VAULT_DIR — skipping"
else
    cp -r "$REPO_DIR/vault-template" "$VAULT_DIR"

    # Init git repo for vault
    cd "$VAULT_DIR"
    git init
    git add -A
    git commit -m "Initial vault structure"
    log "Vault created at $VAULT_DIR (git initialized)"

    echo ""
    warn "To sync vault with a remote repo:"
    warn "  cd $VAULT_DIR"
    warn "  git remote add origin <your-repo-url>"
    warn "  git push -u origin main"
    echo ""
fi

# ─────────────────────────────────────────────────
# 7. Configure Claude Code
# ─────────────────────────────────────────────────
log "Configuring Claude Code..."

# Create directories
mkdir -p "$CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/projects/-root/memory"

# MCP config
UV_PATH="$UV_BIN"
if [ ! -f "$HOME_DIR/.mcp.json" ]; then
    cat > "$HOME_DIR/.mcp.json" << MCPEOF
{
  "mcpServers": {
    "brain": {
      "command": "$UV_PATH",
      "args": ["run", "--directory", "$BRAIN_DIR", "python", "-m", "brain"],
      "type": "stdio"
    }
  }
}
MCPEOF
    log "MCP config created at ~/.mcp.json"
else
    warn "~/.mcp.json already exists — not overwriting"
fi

# Claude Code settings
if [ ! -f "$CLAUDE_DIR/settings.json" ]; then
    cp "$REPO_DIR/templates/settings.json" "$CLAUDE_DIR/settings.json"
    log "Settings copied to ~/.claude/settings.json"
else
    warn "~/.claude/settings.json already exists — not overwriting"
fi

# CLAUDE.md
if [ ! -f "$HOME_DIR/CLAUDE.md" ]; then
    cp "$REPO_DIR/templates/CLAUDE.md" "$HOME_DIR/CLAUDE.md"
    log "CLAUDE.md copied to ~/CLAUDE.md"
    warn "Edit ~/CLAUDE.md to customize for your workflow"
else
    warn "~/CLAUDE.md already exists — not overwriting"
fi

# Memory template
if [ ! -f "$CLAUDE_DIR/projects/-root/memory/MEMORY.md" ]; then
    cp "$REPO_DIR/templates/memory/MEMORY.md" "$CLAUDE_DIR/projects/-root/memory/MEMORY.md"
    log "Memory template copied"
fi

# Example skill
if [ ! -d "$CLAUDE_DIR/skills/example" ]; then
    cp -r "$REPO_DIR/skills/example" "$CLAUDE_DIR/skills/example"
    log "Example skill copied to ~/.claude/skills/example/"
fi

# ─────────────────────────────────────────────────
# 8. Set up cron jobs
# ─────────────────────────────────────────────────
log "Setting up cron jobs..."

CRON_MARKER="# claude-server-kit"
if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
    warn "Cron jobs already configured — skipping"
else
    # Add vault sync every 5 minutes
    (crontab -l 2>/dev/null || true; cat << CRONEOF

$CRON_MARKER
# Vault git sync every 5 minutes
*/5 * * * * bash $BRAIN_DIR/scripts/vault-sync.sh >> $BRAIN_DIR/logs/vault-sync.log 2>&1
CRONEOF
    ) | crontab -
    log "Cron jobs installed (vault sync every 5 min)"
fi

# ─────────────────────────────────────────────────
# 9. Download ML models
# ─────────────────────────────────────────────────
log "Downloading embedding model (for semantic search)..."
cd "$BRAIN_DIR"
uv run python scripts/download_model.py

# ─────────────────────────────────────────────────
# 10. Start services
# ─────────────────────────────────────────────────
log "Starting Brain services via PM2..."
cd "$BRAIN_DIR"
pm2 start ecosystem.config.cjs
pm2 save

echo ""
echo "═══════════════════════════════════════════════"
echo ""
log "Setup complete!"
echo ""
echo "  Brain MCP:  $BRAIN_DIR"
echo "  Vault:      $VAULT_DIR"
echo "  CLAUDE.md:  $HOME_DIR/CLAUDE.md"
echo "  MCP config: $HOME_DIR/.mcp.json"
echo ""
echo "Next steps:"
echo "  1. Configure Takopi: run 'takopi' and follow the setup wizard"
echo "  2. Edit ~/CLAUDE.md — customize for your workflow"
echo "  3. (Optional) Set up Groq API key for long audio transcription:"
echo "     echo '{\"api_key\": \"your-key\"}' > ~/.groq-api-key.json && chmod 600 ~/.groq-api-key.json"
echo "  4. (Optional) Set up vault remote: cd ~/vault && git remote add origin <url>"
echo "  5. Start Claude Code and say hi!"
echo ""
echo "═══════════════════════════════════════════════"
