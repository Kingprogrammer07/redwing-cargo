"""
Main entry point for the Cargo Tracker Telegram Bot.
Initializes all components and starts polling.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BASE_DIR, BOT_TOKEN, DATABASE_PATH, UPLOADS_DIR
from bot.database import DatabaseManager
from bot.handlers import register_handlers

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    """Configure logging for the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Reduce noise from external libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def _ensure_directories() -> None:
    """Create required directories if they don't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    logger.info("Directories ensured: data=%s, uploads=%s", DATABASE_PATH, UPLOADS_DIR)


async def _init_database() -> DatabaseManager:
    """Initialize the SQLite database."""
    db = DatabaseManager(DATABASE_PATH)
    await db.init_db()
    logger.info("Database initialized")
    return db


def _check_config() -> None:
    """Validate essential configuration before starting."""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error("❌ BOT_TOKEN is not set! Please configure it in .env file.")
        logger.error("   Create .env file with: BOT_TOKEN=your_bot_token_here")
        sys.exit(1)


async def main() -> None:
    """Main async entry point."""
    _setup_logging()
    logger.info("🚀 Starting Cargo Tracker Bot...")

    # Validate config
    _check_config()

    # Ensure directories exist
    _ensure_directories()

    # Initialize database
    db = await _init_database()

    # Create bot instance
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Create dispatcher with memory storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register all handlers
    register_handlers(dp)
    logger.info("Handlers registered")

    # Start polling
    logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Polling error: %s", e)
    finally:
        await bot.session.close()
        await db.close()
        logger.info("🛑 Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
