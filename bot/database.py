"""
Async SQLite database manager using aiosqlite.
Singleton pattern with proper connection management.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Final, List, Optional

import aiosqlite

from bot.models import CargoItem, FlightConfig

logger = logging.getLogger(__name__)

# ─── SQL Constants: cargo_items ─────────────────────────────────────────────

_CREATE_TABLE_SQL: str = """
CREATE TABLE IF NOT EXISTS cargo_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    received_date TEXT NOT NULL,
    track_code TEXT NOT NULL UNIQUE,
    product_name_cn TEXT NOT NULL DEFAULT '',
    product_name_ru TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 1,
    weight REAL NOT NULL DEFAULT 0,
    client_code TEXT NOT NULL DEFAULT '',
    box_number TEXT NOT NULL DEFAULT '',
    flight_name TEXT NOT NULL DEFAULT ''
)
"""

_CREATE_INDEX_TRACK_SQL: str = (
    "CREATE INDEX IF NOT EXISTS idx_track_code ON cargo_items(track_code)"
)
_CREATE_INDEX_CLIENT_SQL: str = (
    "CREATE INDEX IF NOT EXISTS idx_client_code ON cargo_items(client_code)"
)
_CREATE_INDEX_FLIGHT_SQL: str = (
    "CREATE INDEX IF NOT EXISTS idx_flight_name ON cargo_items(flight_name)"
)

_INSERT_OR_REPLACE_SQL: str = """
INSERT OR REPLACE INTO cargo_items 
    (received_date, track_code, product_name_cn, product_name_ru, quantity, weight, client_code, box_number, flight_name)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_SELECT_BY_TRACK_SQL: str = """
SELECT id, received_date, track_code, product_name_cn, product_name_ru, 
       quantity, weight, client_code, box_number, flight_name 
FROM cargo_items 
WHERE track_code LIKE ?
ORDER BY received_date DESC
"""

_SELECT_BY_CLIENT_SQL: str = """
SELECT id, received_date, track_code, product_name_cn, product_name_ru, 
       quantity, weight, client_code, box_number, flight_name 
FROM cargo_items 
WHERE client_code LIKE ?
ORDER BY received_date DESC
"""

_SELECT_BY_FLIGHT_SQL: str = """
SELECT id, received_date, track_code, product_name_cn, product_name_ru, 
       quantity, weight, client_code, box_number, flight_name 
FROM cargo_items 
WHERE flight_name = ?
ORDER BY received_date DESC
"""

_COUNT_SQL: str = "SELECT COUNT(*) FROM cargo_items"
_COUNT_BY_FLIGHT_SQL: str = "SELECT COUNT(*) FROM cargo_items WHERE flight_name = ?"
_DELETE_ALL_SQL: str = "DELETE FROM cargo_items"
_DELETE_BY_FLIGHT_SQL: str = "DELETE FROM cargo_items WHERE flight_name = ?"

# ─── SQL Constants: flight_config ───────────────────────────────────────────

_CREATE_FLIGHT_CONFIG_SQL: str = """
CREATE TABLE IF NOT EXISTS flight_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    updated_at TEXT
)
"""

_GET_FLIGHT_SQL: str = "SELECT id, name, updated_at FROM flight_config WHERE id = 1"
_SET_FLIGHT_SQL: str = """
INSERT INTO flight_config (id, name, updated_at)
VALUES (1, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    updated_at = excluded.updated_at
"""


class DatabaseManager:
    """Async SQLite database manager.
    
    Uses Singleton pattern. Each operation creates and closes its own connection.
    """

    _instance: Optional["DatabaseManager"] = None
    _initialized: bool = False

    def __new__(cls, db_path: Optional[str] = None) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is not None:
            self._db_path: str = db_path
        elif not hasattr(self, "_db_path"):
            from bot.config import DATABASE_PATH
            self._db_path: str = DATABASE_PATH

    # ─── Schema Management ─────────────────────────────────────────────────

    async def init_db(self) -> None:
        """Initialize database: create tables and indexes."""
        if DatabaseManager._initialized:
            return

        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(_CREATE_TABLE_SQL)
            await conn.execute(_CREATE_INDEX_TRACK_SQL)
            await conn.execute(_CREATE_INDEX_CLIENT_SQL)
            await conn.execute(_CREATE_INDEX_FLIGHT_SQL)
            await conn.execute(_CREATE_FLIGHT_CONFIG_SQL)
            await conn.commit()

        DatabaseManager._initialized = True
        logger.info("Database initialized: %s", self._db_path)

    async def close(self) -> None:
        """Reset initialization flag (cleanup)."""
        DatabaseManager._initialized = False

    # ─── Cargo CRUD ─────────────────────────────────────────────────────────

    async def insert_cargo_items(self, items: List[CargoItem]) -> int:
        """Insert or replace cargo items in batch.
        
        Args:
            items: List of CargoItem to insert.
            
        Returns:
            Number of items inserted.
        """
        if not items:
            return 0

        data = [
            (
                item.received_date.isoformat(),
                item.track_code,
                item.product_name_cn,
                item.product_name_ru,
                item.quantity,
                item.weight,
                item.client_code,
                item.box_number,
                item.flight_name,
            )
            for item in items
        ]

        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.executemany(_INSERT_OR_REPLACE_SQL, data)
            await conn.commit()

        logger.info("Inserted %d cargo items", len(items))
        return len(items)

    async def find_by_track_code(self, track_code: str) -> List[CargoItem]:
        """Search cargo items by track code (partial match)."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_SELECT_BY_TRACK_SQL, (f"%{track_code}%",)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_model(row) for row in rows]

    async def find_by_client_code(self, client_code: str) -> List[CargoItem]:
        """Search cargo items by client code (partial match)."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_SELECT_BY_CLIENT_SQL, (f"%{client_code}%",)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_model(row) for row in rows]

    async def find_by_flight(self, flight_name: str) -> List[CargoItem]:
        """Search cargo items by exact flight name."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_SELECT_BY_FLIGHT_SQL, (flight_name,)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_model(row) for row in rows]

    async def delete_all_items(self) -> int:
        """Delete all cargo items from the database."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(_DELETE_ALL_SQL)
            await conn.commit()
            deleted = cursor.rowcount if cursor.rowcount is not None else 0
            logger.info("Deleted all %d cargo items", deleted)
            return deleted

    async def delete_by_flight(self, flight_name: str) -> int:
        """Delete cargo items by flight name.
        
        Args:
            flight_name: Flight name to delete by.
            
        Returns:
            Number of rows deleted.
        """
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(_DELETE_BY_FLIGHT_SQL, (flight_name,))
            await conn.commit()
            deleted = cursor.rowcount if cursor.rowcount is not None else 0
            logger.info("Deleted %d items for flight '%s'", deleted, flight_name)
            return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_COUNT_SQL) as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0
                return {"total": total}

    async def get_flight_stats(self, flight_name: str) -> Dict[str, Any]:
        """Get statistics for a specific flight."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_COUNT_BY_FLIGHT_SQL, (flight_name,)) as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0
                return {"total": total}

    async def get_all_flights(self) -> List[str]:
        """Get list of all unique flight names."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT DISTINCT flight_name FROM cargo_items WHERE flight_name != '' ORDER BY flight_name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    # ─── Flight Config ──────────────────────────────────────────────────────

    async def get_flight_config(self) -> Optional[FlightConfig]:
        """Get current flight configuration."""
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(_GET_FLIGHT_SQL) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                updated_at = row["updated_at"]
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(updated_at)
                    except ValueError:
                        updated_at = None
                return FlightConfig(
                    id=row["id"],
                    name=row["name"] or "",
                    updated_at=updated_at,
                )

    async def set_flight_config(self, name: str) -> None:
        """Set current flight configuration."""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(_SET_FLIGHT_SQL, (name, now))
            await conn.commit()
        logger.info("Flight config set: %s", name)

    # ─── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_model(row: aiosqlite.Row) -> CargoItem:
        """Convert a database row to a CargoItem model."""
        received_date = row["received_date"]
        if isinstance(received_date, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
            ):
                try:
                    received_date = datetime.strptime(received_date, fmt)
                    break
                except ValueError:
                    continue
            else:
                received_date = datetime.now()

        return CargoItem(
            id=row["id"],
            received_date=received_date,
            track_code=row["track_code"] or "",
            product_name_cn=row["product_name_cn"] or "",
            product_name_ru=row["product_name_ru"] or "",
            quantity=row["quantity"] or 1,
            weight=row["weight"] or 0.0,
            client_code=row["client_code"] or "",
            box_number=row["box_number"] or "",
            flight_name=row["flight_name"] or "",
        )
