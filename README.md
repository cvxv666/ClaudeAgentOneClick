![Claude Server Kit](docs/images/social-preview.png)

# Claude Server Kit

[![CI](https://github.com/doffskiii/claude-server-kit/actions/workflows/test-setup.yml/badge.svg)](https://github.com/doffskiii/claude-server-kit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-6e1cff.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-6e1cff.svg)](https://claude.ai)

> **TL;DR for agents:** `git clone https://github.com/doffskiii/claude-server-kit.git && cd claude-server-kit && bash setup.sh && bash configure.sh && claude`

Turn your VPS into a personal AI assistant with persistent memory, a Telegram bot, and a bunch of superpowers.

Two weeks of daily iterations, packaged into one repository. Clone it, run `setup.sh`, and get an agent that remembers everything, manages tasks, transcribes voice messages, and chats with you on Telegram.

> Detailed post series covering every component: [Course for young AI builders](https://t.me/yshlfe/264)

![Architecture](docs/images/architecture.png)

---

## Table of Contents

- [What's Inside](#whats-inside)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Credentials Setup](#credentials-setup)
- [Repository Structure](#repository-structure)
- [Brain MCP — 20 Tools](#brain-mcp--20-tools)
- [Takopi (Telegram Bot)](#takopi-telegram-bot)
- [Vault Conventions](#vault-conventions)
- [Under the Hood](#under-the-hood)
- [Creating Skills](#creating-skills)
- [Auto-Memory](#auto-memory)
- [Monitoring](#monitoring)
- [Backups](#backups)
- [Librarian](#librarian)

---

## What's Inside

- **Brain MCP** — 20 tools for memory management: search (keyword + semantic), write, dashboard, audio transcription, calendar, server monitoring
- **Vault** — Obsidian knowledge base with git sync, YAML metadata, bidirectional links, and a context file in every folder
- **Semantic Search** — finds documents by meaning, not just keywords. ONNX model, runs on CPU
- **Whisper** — OpenAI-compatible transcription server. Short audio processed locally, long recordings routed to Groq API
- **Takopi** — Telegram bot for chatting with the agent from your phone. Voice messages, files, multi-sessions
- **Monitoring** — Telegram alerts when CPU/RAM/disk hits limits or a process crashes
- **Librarian** — weekly autonomous vault audit: finds orphans, broken links, stale files
- **Dual-Channel Ask** — questions sent simultaneously to VS Code and Telegram. First to respond wins
- **Context7** — up-to-date documentation for any library on demand
- **Skills** — extensible command system for repeating tasks
- **Escalating Reminders** — cron reminders that get more insistent with each level
- **Interactive Onboarding** — agent walks new users through all setup steps, no docs required

## Quick Start

```bash
# 1. Clone
git clone https://github.com/doffskiii/claude-server-kit.git
cd claude-server-kit

# 2. Install everything (uv, Node.js, PM2, Brain, vault, ML models)
bash setup.sh

# 3. Configure credentials (interactive wizard)
bash configure.sh

# 4. Launch Claude Code and type "hello"
claude
```

![Onboarding Flow](docs/images/onboarding-flow.png)

The agent will detect it's a first run and launch **interactive onboarding**: it will introduce itself, explain what it can do, set up Telegram, voice, backups, and security. Just answer the questions.

## Requirements

- Ubuntu 20.04+ (or equivalent Linux)
- 2+ GB RAM (4+ GB if you want Whisper + embeddings)
- Git, internet connection
- `setup.sh` installs everything else: uv, Python 3.12+, Node.js, PM2, ffmpeg

## Credentials Setup

Use the wizard `bash configure.sh`, or configure manually:

**Takopi (Telegram bot)** — required for chatting from your phone
```bash
uv tool install takopi && takopi
```

**Groq API (optional)** — speeds up transcription of long audio
```bash
echo '{"api_key":"gsk_..."}' > ~/.groq-api-key.json && chmod 600 ~/.groq-api-key.json
```

**Git vault backup (optional)** — pushes vault to a private repo every 5 minutes
```bash
cd ~/vault && git remote add origin git@github.com:you/vault-private.git
```

**Encrypted backup (optional)** — daily full backup with GPG
```bash
echo 'your-passphrase' > ~/.backup-passphrase && chmod 600 ~/.backup-passphrase
```

All sensitive files — `chmod 600` and in `.gitignore`.

<details>
<summary><b>Repository Structure</b></summary>

```
claude-server-kit/
├── brain/                    # Brain MCP server (Python, FastMCP)
│   ├── src/brain/
│   │   ├── server.py         # 20 MCP tools
│   │   ├── config.py         # Configuration (env-driven)
│   │   ├── whisper_server.py # OpenAI-compatible Whisper API
│   │   ├── vault/            # Vault operations
│   │   ├── calendar/         # Calendar (SQLite)
│   │   └── server_tools/     # Server monitoring
│   ├── scripts/              # Utilities
│   └── ecosystem.config.cjs  # PM2 configuration
│
├── librarian/                # Autonomous vault auditing
│   ├── SYSTEM.md             # Agent system prompt
│   ├── CHECKLIST.md          # 10-section checklist
│   └── run.sh                # Cron entry point
│
├── vault-template/           # Empty vault with context files
│   ├── dashboard.md          # Task dashboard
│   ├── inbox/                # Incoming ideas
│   ├── conversations/        # Session notes
│   ├── decisions/            # Decision log
│   ├── knowledge/            # Knowledge (projects, personal, learning)
│   ├── retro/                # Retrospectives
│   └── templates/            # Obsidian templates
│
├── templates/                # Claude Code config templates
│   ├── CLAUDE.md             # Agent instructions (THE BRAIN)
│   ├── mcp.json              # MCP server registration
│   ├── settings.json         # Permissions configuration
│   └── memory/MEMORY.md      # Auto-memory bootstrap
│
├── scripts/                  # Server automation
│   ├── backup.sh             # Encrypted backup (GPG AES-256)
│   ├── git-push-all.sh       # Daily code push to GitHub
│   ├── calendar-sync.py      # Calendar sync (hourly)
│   └── reminders/            # Escalating reminders
│
├── skills/                   # Claude Code skill examples
│   ├── onboarding/SKILL.md   # Interactive onboarding
│   ├── track/SKILL.md        # Smart task routing
│   └── reflect/SKILL.md      # Daily reflection
│
├── setup.sh                  # One-command installation
├── configure.sh              # Interactive credentials wizard
└── .gitignore
```

</details>

<details>
<summary><b>Brain MCP — 20 Tools</b></summary>

**Vault:** `search_vault` (full-text search) / `semantic_search` (meaning-based search) / `read_vault` / `write_vault` (with auto-metadata and git sync) / `list_vault` / `update_dashboard` (safe update, never overwrites)

**Ingest:** `ingest_audio` (audio to text, local or via Groq) / `ingest_document` (PDF/text with auto-chunking)

**Calendar:** `get_today` (current date + 03:00 day boundary + week) / `add_calendar_event` / `list_calendar_events` / `remove_calendar_event` / `update_calendar_event` / `queue_calendar_sync`

**Telegram:** `send_telegram_question` (non-blocking) / `check_telegram_answer` (polling) / `cancel_telegram_question` / `ask_via_telegram` (blocking, legacy)

**Server:** `get_server_status` (CPU/RAM/disk/PM2) / `get_server_map` (service map)

</details>

## Takopi (Telegram Bot)

[Takopi](https://github.com/miilv/takopi) — open-source bridge between Telegram and AI agents.

- Multi-engine: Claude Code, Codex, OpenCode, DeepSeek
- Voice message transcription (routed to Brain Whisper)
- File transfer, multi-sessions, streaming
- Dual-channel Q&A server on port 9877
- Install: `uv tool install -U takopi`

## Vault Conventions

- **Context files** — each folder has a `FOLDER_NAME.md` that indexes its contents
- **Frontmatter** — all files have YAML metadata: title, tags, created, source
- **Bidirectional links** — if A links to B, then B must link to A
- **Dashboard** — only via `update_dashboard()`, never via `write_vault("dashboard.md")`
- **Decisions** — important decisions saved to `decisions/YYYY-MM-DD_slug.md`
- **Session notes** — after VS Code work, saved to `conversations/YYYY-MM-DD_slug.md`
- **03:00 day boundary** — for night owls: logical day ends at 3 AM, not midnight

<details>
<summary><b>Under the Hood</b></summary>

**Debounced Git Sync** — multiple writes within 30 seconds are batched into one commit. Fire-and-forget, doesn't block responses.

**Incremental Embeddings** — when a document is written, only its embeddings are recalculated. No full index rebuild needed.

**Thread-Safe ONNX** — global lock prevents concurrent access to the embedding model. Safe for parallel tool calls.

**Fail-Safe Calendar Sync** — events are linked to task systems via `source_type` + `source_id`. Hourly cron verifies task completion before removing events.

**Escalating Reminders** — 4 levels: detailed stats → simple nudge → last chance → auto-execute. Marker files prevent duplicate runs.

**Path Security** — all vault paths validated against directory traversal and symlink attacks. `.env`, `.ssh`, tokens blocked from ingestion.

</details>

## Creating Skills

Skills are instruction files that extend agent capabilities:

```
~/.claude/skills/my-skill/
├── SKILL.md      # Instructions + triggers
└── scripts/      # Helper scripts (optional)
```

See `skills/onboarding/SKILL.md` for an example, `skills/track/SKILL.md` and `skills/reflect/SKILL.md` for production skills.

## Auto-Memory

Claude Code stores knowledge between sessions in `~/.claude/projects/<project>/memory/`:

- `MEMORY.md` — key rules, always loaded into context (keep under 200 lines)
- Topic files (`whisper.md`, `trello.md`) — detailed domain knowledge, loaded on demand
- Claude updates these files automatically as you work

## Monitoring

Brain Monitor (PM2 daemon) sends Telegram alerts when:
- CPU > 80% three checks in a row
- Available RAM < 1 GB
- Disk > 85%
- Any PM2 process crashes

30-minute cooldown between identical alerts.

## Backups

Three layers:
1. **Vault git sync** (every 5 min) — continuous knowledge backup
2. **Code git push** (daily) — all repositories to GitHub
3. **Encrypted backup** (daily) — GPG AES-256 → cloud

## Librarian

Weekly autonomous agent that audits the vault:
- Missing context files, orphans, broken links
- Stale entries, bidirectional link violations
- Frontmatter issues, freshness scoring
- Sends compressed report to Telegram

Cron: `0 4 * * 1 bash ~/librarian/run.sh` (Monday, 4 AM).

<details>
<summary><b>Environment Variables</b></summary>

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAIN_VAULT_PATH` | `~/vault` | Path to Obsidian vault |
| `TAKOPI_CONFIG` | `~/.takopi/takopi.toml` | Takopi config |
| `GROQ_KEY_FILE` | `~/.groq-api-key.json` | Groq API key for long audio |

</details>

## Credits

- [Takopi](https://github.com/miilv/takopi) by banteg — Telegram bridge for AI agents
- [FastMCP](https://github.com/jlowin/fastmcp) — lightweight MCP framework
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 Whisper
- [Obsidian](https://obsidian.md) — knowledge management
- [sentence-transformers](https://www.sbert.net/) — multilingual embeddings

## License

MIT

---

Like it? Drop a star — it helps others find the project!
