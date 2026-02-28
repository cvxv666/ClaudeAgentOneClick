#!/usr/bin/env bash
# Claude Server Kit — interactive configuration wizard.
#
# Run after setup.sh to configure all API keys and credentials.
# Safe to re-run — only overwrites what you confirm.
#
# Usage: bash configure.sh

set -euo pipefail

HOME_DIR="${HOME:-/root}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

log()   { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
info()  { echo -e "${CYAN}[i]${NC} $*"; }
err()   { echo -e "${RED}[x]${NC} $*"; }
header() { echo -e "\n${BOLD}═══ $* ═══${NC}\n"; }

ask_yn() {
    local prompt="$1" default="${2:-n}"
    local yn
    if [[ "$default" == "y" ]]; then
        read -rp "$prompt [Y/n] " yn
        yn="${yn:-y}"
    else
        read -rp "$prompt [y/N] " yn
        yn="${yn:-n}"
    fi
    [[ "$yn" =~ ^[Yy] ]]
}

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     Claude Server Kit — Configuration    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
info "This wizard will help you set up all API keys and credentials."
info "Each step is optional — skip what you don't need yet."
echo ""

# ─────────────────────────────────────────────
# 1. CLAUDE.md — Owner info
# ─────────────────────────────────────────────
header "1/6 — Your Identity (CLAUDE.md)"

CLAUDE_MD="$HOME_DIR/CLAUDE.md"
if [ -f "$CLAUDE_MD" ]; then
    current_owner=$(grep "^Owner:" "$CLAUDE_MD" 2>/dev/null || echo "")
    if echo "$current_owner" | grep -q "YOUR_NAME"; then
        info "CLAUDE.md has placeholder owner info — let's fix that."
        read -rp "Your name (e.g. Alex): " YOUR_NAME
        if [ -n "$YOUR_NAME" ]; then
            read -rp "Your Telegram user ID (numeric, find via @userinfobot): " YOUR_TG_ID
            YOUR_TG_ID="${YOUR_TG_ID:-0}"
            sed -i "s/YOUR_NAME/$YOUR_NAME/g" "$CLAUDE_MD"
            sed -i "s/YOUR_TG_ID/$YOUR_TG_ID/g" "$CLAUDE_MD"
            log "CLAUDE.md updated with your info"
        else
            warn "Skipped — edit ~/CLAUDE.md manually later"
        fi
    else
        log "CLAUDE.md already configured: $current_owner"
    fi
else
    warn "~/CLAUDE.md not found — run setup.sh first"
fi

# ─────────────────────────────────────────────
# 2. Takopi — Telegram Bot
# ─────────────────────────────────────────────
header "2/6 — Takopi (Telegram Bot)"

if command -v takopi &>/dev/null; then
    if [ -f "$HOME_DIR/.takopi/takopi.toml" ]; then
        log "Takopi already configured"
        info "To reconfigure: rm ~/.takopi/takopi.toml && takopi"
    else
        info "Takopi is installed but not configured yet."
        echo ""
        info "You need:"
        info "  1. A Telegram bot token (get from @BotFather)"
        info "  2. Your Telegram chat ID (get from @userinfobot)"
        echo ""
        if ask_yn "Configure Takopi now?"; then
            echo ""
            info "Running Takopi setup wizard..."
            echo ""
            takopi || warn "Takopi setup failed — try running 'takopi' manually"
        else
            warn "Skipped — run 'takopi' when ready"
        fi
    fi
else
    warn "Takopi not installed — run setup.sh first, or: uv tool install -U takopi"
fi

# ─────────────────────────────────────────────
# 3. Groq API Key (optional — for long audio)
# ─────────────────────────────────────────────
header "3/6 — Groq API Key (optional)"

GROQ_FILE="$HOME_DIR/.groq-api-key.json"
if [ -f "$GROQ_FILE" ]; then
    log "Groq API key already configured at $GROQ_FILE"
else
    info "Groq API provides fast Whisper transcription for audio >4 minutes."
    info "Without it, all audio is transcribed locally (slower for long files)."
    info "Get a free key at: https://console.groq.com/keys"
    echo ""
    if ask_yn "Set up Groq API key?"; then
        read -rp "Groq API key (gsk_...): " GROQ_KEY
        if [ -n "$GROQ_KEY" ]; then
            echo "{\"api_key\": \"$GROQ_KEY\"}" > "$GROQ_FILE"
            chmod 600 "$GROQ_FILE"
            log "Groq API key saved to $GROQ_FILE (chmod 600)"
        else
            warn "Empty key — skipped"
        fi
    else
        warn "Skipped — local Whisper will handle all audio"
    fi
fi

# ─────────────────────────────────────────────
# 4. Vault Git Remote (optional)
# ─────────────────────────────────────────────
header "4/6 — Vault Git Remote (optional)"

VAULT_DIR="${BRAIN_VAULT_PATH:-$HOME_DIR/vault}"
if [ -d "$VAULT_DIR/.git" ]; then
    remote=$(cd "$VAULT_DIR" && git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$remote" ]; then
        log "Vault remote already set: $remote"
    else
        info "Your vault can sync to a private Git repo for backup."
        info "Create a PRIVATE repo on GitHub/GitLab first."
        echo ""
        if ask_yn "Set up vault git remote?"; then
            read -rp "Remote URL (e.g. git@github.com:user/vault.git): " VAULT_REMOTE
            if [ -n "$VAULT_REMOTE" ]; then
                cd "$VAULT_DIR"
                git remote add origin "$VAULT_REMOTE"
                log "Vault remote added: $VAULT_REMOTE"
                info "First push: cd ~/vault && git push -u origin main"
            else
                warn "Empty URL — skipped"
            fi
        else
            warn "Skipped — vault stays local only"
        fi
    fi
else
    warn "Vault not initialized — run setup.sh first"
fi

# ─────────────────────────────────────────────
# 5. Backup Passphrase
# ─────────────────────────────────────────────
header "5/6 — Backup Encryption (optional)"

PASSPHRASE_FILE="$HOME_DIR/.backup-passphrase"
if [ -f "$PASSPHRASE_FILE" ]; then
    log "Backup passphrase already set"
else
    info "The backup script encrypts your data with a GPG passphrase."
    info "Without it, backups won't work."
    echo ""
    if ask_yn "Set up backup passphrase?"; then
        read -rsp "Enter backup passphrase (won't be displayed): " PASSPHRASE
        echo ""
        if [ -n "$PASSPHRASE" ]; then
            echo "$PASSPHRASE" > "$PASSPHRASE_FILE"
            chmod 600 "$PASSPHRASE_FILE"
            log "Passphrase saved to $PASSPHRASE_FILE (chmod 600)"
            warn "REMEMBER THIS PASSPHRASE — you need it to restore backups!"
        else
            warn "Empty passphrase — skipped"
        fi
    else
        warn "Skipped — set up later with: echo 'passphrase' > ~/.backup-passphrase && chmod 600 ~/.backup-passphrase"
    fi
fi

# ─────────────────────────────────────────────
# 6. Additional MCP Servers
# ─────────────────────────────────────────────
header "6/6 — Additional MCP Servers (optional)"

info "You can add more MCP servers for external services."
info "Popular options:"
echo ""
echo "  Figma:     npx -y figma-developer-mcp --figma-api-key=YOUR_KEY --stdio"
echo "  GitHub:    npx -y @anthropic/mcp-github --token=YOUR_TOKEN"
echo "  Postgres:  npx -y @anthropic/mcp-postgres postgres://..."
echo ""
info "Edit ~/.mcp.json to add servers. Example:"
echo ""
echo '  {
    "mcpServers": {
      "brain": { ... },
      "figma": {
        "command": "npx",
        "args": ["-y", "figma-developer-mcp", "--figma-api-key=YOUR_KEY", "--stdio"],
        "type": "stdio"
      }
    }
  }'
echo ""

MCP_FILE="$HOME_DIR/.mcp.json"
if ask_yn "Add Figma MCP server now?"; then
    read -rp "Figma API key (figd_...): " FIGMA_KEY
    if [ -n "$FIGMA_KEY" ]; then
        # Add figma server to existing .mcp.json
        if [ -f "$MCP_FILE" ] && command -v python3 &>/dev/null; then
            python3 -c "
import json
with open('$MCP_FILE') as f:
    config = json.load(f)
config['mcpServers']['figma'] = {
    'command': 'npx',
    'args': ['-y', 'figma-developer-mcp', '--figma-api-key=$FIGMA_KEY', '--stdio'],
    'type': 'stdio'
}
with open('$MCP_FILE', 'w') as f:
    json.dump(config, f, indent=2)
print('Done')
"
            log "Figma MCP added to ~/.mcp.json"
            # Add Figma permissions to settings
            SETTINGS="$HOME_DIR/.claude/settings.json"
            if [ -f "$SETTINGS" ]; then
                python3 -c "
import json
with open('$SETTINGS') as f:
    config = json.load(f)
perms = config.get('permissions', {}).get('allow', [])
if 'mcp__figma__*' not in perms:
    perms.append('mcp__figma__*')
    config['permissions']['allow'] = perms
    with open('$SETTINGS', 'w') as f:
        json.dump(config, f, indent=2)
    print('Permissions updated')
else:
    print('Already in permissions')
"
            fi
        else
            warn "Manual step: add Figma to ~/.mcp.json"
        fi
    fi
fi

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║          Configuration Complete!         ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

echo "Status:"

# Check each component
check() {
    local name="$1" file="$2"
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${YELLOW}○${NC} $name (not configured)"
    fi
}

check "CLAUDE.md"          "$HOME_DIR/CLAUDE.md"
check "Takopi"             "$HOME_DIR/.takopi/takopi.toml"
check "Groq API"           "$HOME_DIR/.groq-api-key.json"
check "Backup passphrase"  "$HOME_DIR/.backup-passphrase"
check "MCP config"         "$HOME_DIR/.mcp.json"
check "Claude settings"    "$HOME_DIR/.claude/settings.json"

echo ""

# Check vault remote
if [ -d "$VAULT_DIR/.git" ]; then
    remote=$(cd "$VAULT_DIR" && git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$remote" ]; then
        echo -e "  ${GREEN}✓${NC} Vault remote: $remote"
    else
        echo -e "  ${YELLOW}○${NC} Vault remote (local only)"
    fi
fi

echo ""
info "Re-run this script anytime to update credentials."
info "Start Claude Code with: claude"
echo ""
