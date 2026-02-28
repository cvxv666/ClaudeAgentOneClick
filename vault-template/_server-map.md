---
title: Server Map
tags:
  - server
  - infrastructure
---

# Server Map

## Services

| Service | Port | Manager | Status |
|---------|------|---------|--------|
| Brain MCP | stdio | Claude Code | on-demand |
| Brain Monitor | — | PM2 | always-on |
| Brain Whisper | 8787 | PM2 | always-on |
| Takopi | 9877 (ask) | PM2 | always-on |

## Data Locations

| Data | Path | Notes |
|------|------|-------|
| Vault | ~/vault/ | Obsidian + git sync |
| Brain MCP | ~/brain/ | Python MCP server |
| Takopi config | ~/.takopi/ | Telegram bot config |
| Credentials | ~/. files | chmod 600, never commit |

## Credentials

<!-- UPDATE: List your credential files here (paths only, not values) -->
- `~/.takopi/takopi.toml` — Telegram bot token + chat ID
- `~/.groq-api-key.json` — Groq API key (for long audio transcription)
