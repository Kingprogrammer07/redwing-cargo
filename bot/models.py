"""
Pydantic models for cargo tracking data.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class CargoItem(BaseModel):
    """Represents a single cargo item in the warehouse."""

    id: Optional[int] = None
    received_date: datetime
    track_code: str = Field(..., min_length=1)
    product_name_cn: str = Field(default="")
    product_name_ru: str = Field(default="")
    quantity: int = Field(default=1, ge=1)
    weight: float = Field(default=0.0, ge=0.0)
    client_code: str = Field(default="")
    box_number: str = Field(default="")
    flight_name: str = Field(default="")

    model_config = {"from_attributes": True}

    @field_validator(
        "track_code",
        "product_name_cn",
        "product_name_ru",
        "client_code",
        "box_number",
        "flight_name",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v: Any) -> int:
        if v is None:
            return 1
        try:
            return int(float(str(v).strip()))
        except (ValueError, TypeError):
            return 1

    @field_validator("weight", mode="before")
    @classmethod
    def parse_weight(cls, v: Any) -> float:
        if v is None:
            return 0.0
        try:
            return float(str(v).strip())
        except (ValueError, TypeError):
            return 0.0


class FlightConfig(BaseModel):
    """Represents the current flight configuration."""

    id: Optional[int] = None
    name: str = Field(default="", min_length=1)
    updated_at: Optional[datetime] = None


class TrackSearchResult(BaseModel):
    """Result of a track code search."""

    items: List[CargoItem] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)


class ClientSearchResult(BaseModel):
    """Result of a client code search."""

    items: List[CargoItem] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)


class ImportResult(BaseModel):
    """Result of an Excel import operation."""

    total_rows: int = Field(default=0, ge=0)
    imported: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    errors: List[str] = Field(default_factory=list)
    flight_name: str = Field(default="")
