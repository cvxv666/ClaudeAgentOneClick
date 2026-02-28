"""Configuration for brain MCP server and monitoring daemon.

All paths are configurable via environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

# Vault — override with BRAIN_VAULT_PATH env var
VAULT_PATH = Path(os.environ.get("BRAIN_VAULT_PATH", os.path.expanduser("~/vault")))

# Git sync
SYNC_DEBOUNCE = 30  # seconds — batch writes within this window

# Monitoring thresholds
CPU_THRESHOLD = 80  # percent
CPU_CONSECUTIVE = 3  # checks before alert
RAM_MIN_AVAILABLE_GB = 1.0  # alert if available RAM drops below
DISK_THRESHOLD = 85  # percent

# Monitoring interval
MONITOR_INTERVAL = 300  # seconds (5 minutes)

# Alert cooldown — don't repeat same alert within this period
ALERT_COOLDOWN = 1800  # seconds (30 minutes)

# Semantic search
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384
EMBEDDING_CHUNK_WORDS = 200
EMBEDDING_INDEX_DIR = VAULT_PATH / ".brain"

# Takopi config path (bot_token + chat_id) — override with TAKOPI_CONFIG env var
TAKOPI_CONFIG = Path(os.environ.get("TAKOPI_CONFIG", os.path.expanduser("~/.takopi/takopi.toml")))

# Groq API key file — override with GROQ_KEY_FILE env var
GROQ_KEY_FILE = Path(os.environ.get("GROQ_KEY_FILE", os.path.expanduser("~/.groq-api-key.json")))


def get_telegram_config() -> tuple[str, int]:
    """Read bot_token and chat_id from takopi config."""
    import tomli

    with open(TAKOPI_CONFIG, "rb") as f:
        config = tomli.load(f)

    tg = config["transports"]["telegram"]
    return tg["bot_token"], tg["chat_id"]
