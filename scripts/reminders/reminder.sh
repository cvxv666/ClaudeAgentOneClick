#!/usr/bin/env bash
# Generic reminder with escalation levels.
# Called by cron at different times.
#
# Usage: reminder.sh <name> <level>
#   Level 1: Detailed message
#   Level 2: Nudge
#   Level 3: Yes/No question
#   Level 4: Auto-action
#
# Skips if already done (marker file exists).
#
# Example cron (Sunday retro):
#   0 15 * * 0  /path/to/reminder.sh retro 1
#   0 17 * * 0  /path/to/reminder.sh retro 2
#   0 18 * * 0  /path/to/reminder.sh retro 3
#   30 18 * * 0 /path/to/reminder.sh retro 4

set -euo pipefail

NAME="${1:-reminder}"
LEVEL="${2:-1}"
MARKER_DIR="${HOME}/scripts/reminders/.markers"
BOT_TOKEN="${TG_BOT_TOKEN:-}"
CHAT_ID="${TG_CHAT_ID:-}"

mkdir -p "$MARKER_DIR"

# Get current ISO week
WEEK=$(date +%G-W%V)
MARKER="$MARKER_DIR/${NAME}_done_$WEEK"

# Skip if already done
if [[ -f "$MARKER" ]]; then
    echo "L$LEVEL: $NAME already done for $WEEK, skipping"
    exit 0
fi

# Send message via Telegram (if configured)
send_tg() {
    if [ -n "$BOT_TOKEN" ] && [ -n "$CHAT_ID" ]; then
        curl -s -X POST \
            "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": \"$1\", \"parse_mode\": \"Markdown\"}" \
            > /dev/null
    else
        echo "$1"
    fi
}

case "$LEVEL" in
    1)
        send_tg "*$NAME Reminder (L1)*
Time to do your weekly $NAME!
Check your tasks and get started."
        ;;
    2)
        send_tg "*$NAME Reminder (L2)*
Hey, don't forget about $NAME today!"
        ;;
    3)
        send_tg "*$NAME Reminder (L3)*
Are you going to do $NAME today? Last chance before auto-mode."
        ;;
    4)
        send_tg "*$NAME Auto-Reminder (L4)*
Running $NAME automatically since you didn't respond."
        # Add your auto-action here
        # touch "$MARKER"  # Mark as done after auto-action
        ;;
    *)
        echo "Unknown level: $LEVEL"
        exit 1
        ;;
esac
