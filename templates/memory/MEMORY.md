# Memory

## Core Rules (always apply)

### Dual-Channel Ask
- **NEVER use AskUserQuestion** — it does NOT reach Telegram
- **ALL user questions = dual-channel** (VS Code text + Telegram buttons, first answer wins)
- Workflow: `send_telegram_question` -> print in VS Code -> background poll -> first answer wins

### Session Notes
- After ANY significant work session -> suggest saving session notes
