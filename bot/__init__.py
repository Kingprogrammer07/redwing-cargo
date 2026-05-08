"""
Cargo Tracker Telegram Bot.

Usage:
    python -m bot
    # or
    python bot/main.py

Environment:
    BOT_TOKEN - Required. Telegram bot token from @BotFather.
"""
from __future__ import annotations

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
