# Claude Server Kit

Turn a VPS into an AI-powered personal server with persistent memory, Telegram integration, and knowledge management.

## What You Get

- **Brain MCP Server** — Obsidian vault as Claude's persistent memory. Search, read, write, dashboard, audio transcription, semantic search, server monitoring.
- **Takopi** — Telegram bot that bridges your chat to Claude Code (and other AI agents). Voice messages, file transfer, multi-session support.
- **Dual-Channel** — Ask questions in both VS Code and Telegram simultaneously. First answer wins.
- **Vault** — Structured Obsidian vault with git sync, YAML frontmatter, bidirectional links.
- **Dashboard** — Simple task management directly in the vault.
- **Monitoring** — CPU/RAM/disk alerts to Telegram when things go wrong.
- **Whisper** — Local audio transcription server (short audio local, long audio via Groq API).
- **Semantic Search** — Find documents by meaning, not just keywords (ONNX embeddings, runs on CPU).

## Architecture

```
┌─────────────────────────────────────────┐
│              Claude Code                │
│  CLAUDE.md + MCP Servers + Skills       │
└────────┬──────────────────┬─────────────┘
         │                  │
   ┌─────▼─────┐    ┌──────▼──────┐
   │ Brain MCP │    │   Takopi    │
   │  (vault)  │◄──►│ (Telegram)  │
   └─────┬─────┘    └──────┬──────┘
         │                  │
   ┌─────▼─────┐    ┌──────▼──────┐
   │  ~/vault/ │    │  Telegram   │
   │ (Obsidian)│    │   (you)     │
   └───────────┘    └─────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USER/claude-server-kit.git
cd claude-server-kit

# 2. Run setup (installs everything: uv, Node.js, PM2, Brain, Takopi, vault)
bash setup.sh

# 3. Configure API keys and credentials (interactive wizard)
bash configure.sh

# 4. Start Claude Code
claude
```

## Onboarding: API Keys & Credentials

Run `bash configure.sh` for an interactive wizard, or set up manually:

| What | How | Required? |
|------|-----|-----------|
| **Takopi** (Telegram bot) | `takopi` (interactive setup wizard) | Yes, for Telegram |
| **Groq API** (fast transcription) | `echo '{"api_key":"gsk_..."}' > ~/.groq-api-key.json && chmod 600 ~/.groq-api-key.json` | Optional (long audio) |
| **Vault git remote** | `cd ~/vault && git remote add origin <url>` | Optional (cloud backup) |
| **Backup passphrase** | `echo 'passphrase' > ~/.backup-passphrase && chmod 600 ~/.backup-passphrase` | Optional (backups) |
| **Figma API** | Add to `~/.mcp.json` (see configure.sh) | Optional |
| **CLAUDE.md** | Edit `~/CLAUDE.md` — set your name, customize workflow | Recommended |

All credential files are `chmod 600` and listed in `.gitignore` — they never get committed.

## Requirements

- Ubuntu 20.04+ (or similar Linux)
- 2+ GB RAM (4+ GB recommended for Whisper)
- Git
- Internet access

The setup script installs everything else: uv, Python 3.12+, Node.js, PM2, ffmpeg, etc.

## What's Inside

```
claude-server-kit/
├── brain/                 # Brain MCP server (Python)
│   ├── src/brain/         # MCP tools: vault, ingest, search, monitor
│   ├── scripts/           # Utility scripts
│   └── ecosystem.config.cjs  # PM2 config
├── vault-template/        # Empty vault with context files
├── templates/             # Config templates
│   ├── CLAUDE.md          # Agent instructions
│   ├── mcp.json           # MCP server config
│   ├── settings.json      # Claude Code permissions
│   └── memory/            # Auto-memory template
├── scripts/               # Server scripts (backup, reminders)
├── skills/                # Example Claude Code skills
├── setup.sh               # One-command setup
└── README.md
```

## Brain MCP Tools

| Tool | What it does |
|------|-------------|
| `search_vault` | Full-text regex search across .md files |
| `semantic_search` | Find by meaning (ONNX embeddings) |
| `read_vault` | Read any vault document |
| `write_vault` | Create/update with auto-frontmatter + git sync |
| `list_vault` | List files by folder/tags |
| `update_dashboard` | Safe task management (add/complete/remove) |
| `ingest_audio` | Transcribe audio -> vault (Whisper local + Groq API) |
| `ingest_document` | Process PDF/text -> vault (auto-chunking) |
| `get_server_status` | CPU, RAM, disk, PM2 processes |
| `get_server_map` | Service inventory |
| `send_telegram_question` | Non-blocking Telegram question |
| `check_telegram_answer` | Poll for answer |
| `cancel_telegram_question` | Cancel pending question |
| `ask_via_telegram` | Blocking Telegram question |

## Takopi (Telegram Bot)

[Takopi](https://github.com/miilv/takopi) is an open-source Telegram bridge for AI agents.

**Features:**
- Multi-engine support (Claude Code, Codex, OpenCode, DeepSeek)
- Voice message transcription
- File transfer (upload/download)
- Multi-session conversation history
- Live progress streaming
- Dual-channel Q&A (port 9877)

**Install:** `uv tool install -U takopi`

**Configure:** Run `takopi` for interactive setup, or edit `~/.takopi/takopi.toml`.

## Vault Conventions

**Structure:** Each folder has a `FOLDER_NAME.md` context file that indexes its contents.

**Frontmatter:** Every document has YAML frontmatter (title, tags, created, source).

**Bidirectional links:** When note A links to B, note B should link back to A.

**Dashboard:** Use `update_dashboard()` tool, never overwrite `dashboard.md` directly.

**Decisions:** Save significant decisions to `decisions/YYYY-MM-DD_slug.md`.

**Session notes:** After significant VS Code work, save to `conversations/YYYY-MM-DD_slug.md`.

## Adding Your Own MCP Servers

Edit `~/.mcp.json` to add more MCP servers:

```json
{
  "mcpServers": {
    "brain": { "..." },
    "your-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/server", "python", "-m", "your_server"],
      "type": "stdio"
    }
  }
}
```

Building MCP servers with Python (FastMCP):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(arg: str) -> str:
    """Tool description shown to Claude."""
    return f"Result: {arg}"

mcp.run()
```

## Creating Skills

Skills are instruction files that extend Claude's capabilities:

```
~/.claude/skills/my-skill/
├── SKILL.md      # Instructions + triggers
└── scripts/      # Supporting scripts
```

See `skills/example/SKILL.md` for a template.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAIN_VAULT_PATH` | `~/vault` | Obsidian vault location |
| `TAKOPI_CONFIG` | `~/.takopi/takopi.toml` | Takopi config path |
| `GROQ_KEY_FILE` | `~/.groq-api-key.json` | Groq API key (for long audio) |

## Monitoring

Brain Monitor runs as a PM2 daemon and sends Telegram alerts when:
- CPU > 80% for 3 consecutive checks
- Available RAM < 1 GB
- Disk usage > 85%
- Any PM2 process goes offline

Alerts have a 30-minute cooldown to prevent spam.

## Backup

`scripts/backup.sh` creates an encrypted backup:
1. Saves PM2 config + crontab
2. Archives vault, brain, configs
3. Encrypts with GPG (AES-256)
4. Upload step is customizable (S3, scp, rclone, etc.)

Setup:
```bash
echo 'your-strong-passphrase' > ~/.backup-passphrase
chmod 600 ~/.backup-passphrase
# Add to cron: 0 4 * * * bash ~/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## Credits

- [Takopi](https://github.com/miilv/takopi) by banteg — Telegram bot bridge
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Local speech recognition
- [Obsidian](https://obsidian.md) — Knowledge management (vault is compatible)
