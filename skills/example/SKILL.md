# Example Skill: Send to Telegram

A simple skill that sends files or messages to a Telegram chat via Bot API.

## Triggers

User says: "send to telegram", "share to tg", "send me this"

## How Skills Work

Skills are instructions that Claude Code loads when triggered by matching phrases.
They live in `~/.claude/skills/<name>/SKILL.md` and can include:
- Instructions (this file)
- Scripts (in `scripts/` subfolder)
- Templates
- Any supporting files

## Setup

1. Create `~/.claude/skills/telegram-send/SKILL.md` with your instructions
2. Create `~/.claude/skills/telegram-send/scripts/send.sh`:

```bash
#!/usr/bin/env bash
# Send a file or message to Telegram
# Usage: send.sh file <path> | send.sh message <text>

BOT_TOKEN="${TG_BOT_TOKEN}"
CHAT_ID="${TG_CHAT_ID}"

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "Set TG_BOT_TOKEN and TG_CHAT_ID env vars"
    exit 1
fi

case "$1" in
    file)
        curl -s -F "document=@$2" \
            "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument?chat_id=${CHAT_ID}"
        ;;
    photo)
        curl -s -F "photo=@$2" \
            "https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto?chat_id=${CHAT_ID}"
        ;;
    message)
        curl -s -X POST \
            "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": \"$2\"}"
        ;;
    *)
        echo "Usage: send.sh file|photo|message <content>"
        exit 1
        ;;
esac
```

3. `chmod +x ~/.claude/skills/telegram-send/scripts/send.sh`

## Creating Your Own Skills

1. Create a folder in `~/.claude/skills/your-skill-name/`
2. Write `SKILL.md` with:
   - Clear triggers (when should this skill activate?)
   - Step-by-step instructions for Claude
   - Any scripts or templates needed
3. Reference scripts with absolute paths or relative to the skill folder

### Tips

- Keep SKILL.md focused — one skill, one purpose
- Put reusable logic in scripts, not in the SKILL.md
- Use env vars for credentials, never hardcode
- Test the skill by saying its trigger phrase
