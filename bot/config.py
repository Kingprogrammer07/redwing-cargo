"""
Bot configuration module.
Loads settings from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final, List


def _get_env(key: str, default: str | None = None, required: bool = False) -> str:
    """Get environment variable with validation."""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value or ""


def _parse_admin_ids() -> List[int]:
    """Parse admin IDs from comma-separated env string.
    
    Supports both single ADMIN_ID and comma-separated ADMIN_IDS.
    """
    # Try ADMIN_IDS first (comma-separated), fallback to ADMIN_ID
    ids_str = os.getenv("ADMIN_IDS", "")
    if not ids_str:
        single_id = os.getenv("ADMIN_ID", "777967425")
        ids_str = single_id

    result: List[int] = []
    for part in ids_str.split(","):
        part = part.strip()
        if part:
            try:
                result.append(int(part))
            except ValueError:
                continue
    return result if result else [777967425]


# ─── Admin Configuration ───────────────────────────────────────────────────
ADMINS: Final[List[int]] = _parse_admin_ids()

# ─── Track Code Validation ─────────────────────────────────────────────────
MIN_TRACK_LENGTH: Final[int] = 3
MAX_TRACK_LENGTH: Final[int] = 100
MIN_CLIENT_LENGTH: Final[int] = 2

# ─── Path Configuration ────────────────────────────────────────────────────
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATABASE_PATH: Final[str] = str(BASE_DIR / "data" / "cargo.db")
UPLOADS_DIR: Final[str] = str(BASE_DIR / "uploads")

# ─── Bot Token ─────────────────────────────────────────────────────────────
BOT_TOKEN: Final[str] = _get_env("BOT_TOKEN", required=True)

# ─── Admin Contact ─────────────────────────────────────────────────────────
ADMIN_USERNAME: Final[str] = "MUSTAFOYEV_ANVAR"
ADMIN_CONTACT_URL: Final[str] = f"https://t.me/{ADMIN_USERNAME}"

# ─── Default Flight ────────────────────────────────────────────────────────
DEFAULT_FLIGHT_NAME: Final[str] = "M2 JET"

# ─── Re-export for convenience ─────────────────────────────────────────────
__all__ = [
    "ADMINS",
    "ADMIN_USERNAME",
    "ADMIN_CONTACT_URL",
    "BOT_TOKEN",
    "DATABASE_PATH",
    "UPLOADS_DIR",
    "MIN_TRACK_LENGTH",
    "MAX_TRACK_LENGTH",
    "MIN_CLIENT_LENGTH",
    "DEFAULT_FLIGHT_NAME",
    "BASE_DIR",
]
