"""
Business logic layer — SOLID compliant service implementations.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Final, List, Optional

from bot.config import (
    ADMIN_CONTACT_URL,
    ADMIN_USERNAME,
    MAX_TRACK_LENGTH,
    MIN_CLIENT_LENGTH,
    MIN_TRACK_LENGTH,
)
from bot.database import DatabaseManager
from bot.models import (
    CargoItem,
    ClientSearchResult,
    FlightConfig,
    ImportResult,
    TrackSearchResult,
)
from bot.utils.excel_parser import ExcelParser

logger = logging.getLogger(__name__)


# ─── Abstract Interfaces ───────────────────────────────────────────────────


class CargoService(ABC):
    """Abstract interface for cargo search operations."""

    @abstractmethod
    async def search_by_track(self, track_code: str) -> TrackSearchResult: ...

    @abstractmethod
    async def search_by_client(self, client_code: str) -> ClientSearchResult: ...


class ImportService(ABC):
    """Abstract interface for data import operations."""

    @abstractmethod
    async def import_from_excel(
        self, file_path: str, flight_name: str = ""
    ) -> ImportResult: ...


class FlightConfigService(ABC):
    """Abstract interface for flight configuration management."""

    @abstractmethod
    async def get_current_flight(self) -> Optional[FlightConfig]: ...

    @abstractmethod
    async def set_flight(self, name: str) -> None: ...

    @abstractmethod
    async def get_all_flights(self) -> List[str]: ...


class AdminService(ABC):
    """Abstract interface for admin operations."""

    @abstractmethod
    async def delete_all_items(self) -> int: ...

    @abstractmethod
    async def delete_by_flight(self, flight_name: str) -> int: ...

    @abstractmethod
    async def get_stats(self) -> dict: ...


# ─── Concrete Implementations ──────────────────────────────────────────────


class CargoServiceImpl(CargoService):
    """Concrete implementation of CargoService."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db: Final[DatabaseManager] = db

    async def search_by_track(self, track_code: str) -> TrackSearchResult:
        track_code = track_code.strip()

        if len(track_code) < MIN_TRACK_LENGTH:
            raise ValueError(
                f"Track kod kamida {MIN_TRACK_LENGTH} ta belgidan iborat bo'lishi kerak"
            )
        if len(track_code) > MAX_TRACK_LENGTH:
            raise ValueError(
                f"Track kod {MAX_TRACK_LENGTH} ta belgidan oshmasligi kerak"
            )

        items = await self._db.find_by_track_code(track_code)
        return TrackSearchResult(items=items, total_count=len(items))

    async def search_by_client(self, client_code: str) -> ClientSearchResult:
        client_code = client_code.strip()

        if len(client_code) < MIN_CLIENT_LENGTH:
            raise ValueError(
                f"Client kod kamida {MIN_CLIENT_LENGTH} ta belgidan iborat bo'lishi kerak"
            )

        items = await self._db.find_by_client_code(client_code)
        return ClientSearchResult(items=items, total_count=len(items))


class ImportServiceImpl(ImportService):
    """Concrete implementation of ImportService.
    
    Auto-clears old data before inserting new data.
    Assigns flight_name to all imported items.
    """

    def __init__(self, db: DatabaseManager, parser: ExcelParser) -> None:
        self._db: Final[DatabaseManager] = db
        self._parser: Final[ExcelParser] = parser

    async def import_from_excel(
        self, file_path: str, flight_name: str = ""
    ) -> ImportResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fayl topilmadi: {file_path}")

        # Parse Excel
        items: List[CargoItem] = await self._parser.parse_file(file_path)
        total_rows = len(items)

        if total_rows == 0:
            return ImportResult(
                total_rows=0,
                imported=0,
                skipped=0,
                errors=["Faylda ma'lumot topilmadi"],
                flight_name=flight_name,
            )

        # Filter out items with empty track codes
        valid_items: List[CargoItem] = [
            item for item in items if item.track_code.strip()
        ]
        skipped = total_rows - len(valid_items)

        # Assign flight_name to all items
        for item in valid_items:
            item.flight_name = flight_name

        # FIFO: if flight already exists, delete its old data first
        # (allows re-importing the same flight)
        try:
            await self._db.delete_by_flight(flight_name)
            await self._db.delete_flight_history(flight_name)
        except Exception:
            pass  # Flight didn't exist, that's fine

        # FIFO: if 20 flights exist, delete the oldest one
        try:
            flight_count = await self._db.get_flight_count()
            if flight_count >= 20:
                oldest = await self._db.get_oldest_flight()
                if oldest and oldest != flight_name:
                    deleted = await self._db.delete_by_flight(oldest)
                    await self._db.delete_flight_history(oldest)
                    logger.info(
                        "FIFO: deleted oldest flight '%s' (%d items) to make room",
                        oldest, deleted,
                    )
        except Exception as e:
            logger.warning("FIFO cleanup warning: %s", e)

        # Insert new data
        try:
            imported = await self._db.insert_cargo_items(valid_items)
            await self._db.record_import(flight_name, imported)
            logger.info(
                "Import complete: %d rows imported (flight: %s)",
                imported, flight_name,
            )
        except Exception as e:
            logger.error("Import failed: %s", e)
            return ImportResult(
                total_rows=total_rows,
                imported=0,
                skipped=skipped,
                errors=[f"Bazaga yozishda xatolik: {str(e)}"],
                flight_name=flight_name,
            )

        return ImportResult(
            total_rows=total_rows,
            imported=len(valid_items),
            skipped=skipped,
            errors=[],
            flight_name=flight_name,
        )

    async def cleanup_file(self, file_path: str) -> None:
        """Remove a temporary uploaded file."""
        try:
            os.remove(file_path)
            logger.debug("Cleaned up file: %s", file_path)
        except OSError:
            pass


class FlightConfigServiceImpl(FlightConfigService):
    """Concrete implementation of FlightConfigService."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db: Final[DatabaseManager] = db

    async def get_current_flight(self) -> Optional[FlightConfig]:
        return await self._db.get_flight_config()

    async def set_flight(self, name: str) -> None:
        await self._db.set_flight_config(name.strip())

    async def get_all_flights(self) -> List[str]:
        return await self._db.get_all_flights()


class AdminServiceImpl(AdminService):
    """Concrete implementation of AdminService."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db: Final[DatabaseManager] = db

    async def delete_all_items(self) -> int:
        return await self._db.delete_all_items()

    async def delete_by_flight(self, flight_name: str) -> int:
        return await self._db.delete_by_flight(flight_name)

    async def get_stats(self) -> dict:
        return await self._db.get_stats()
