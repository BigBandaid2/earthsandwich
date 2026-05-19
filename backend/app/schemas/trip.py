from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TripBase(BaseModel):
    title: str
    description: str
    start_date: date
    end_date: date


class TripCreate(TripBase):
    id: str


class TripUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class TripResponse(TripCreate):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripDetailResponse(TripResponse):
    stops: list[StopResponse] = []  # type: ignore[name-defined]  # resolved by model_rebuild()


# Resolved after StopResponse is imported — call TripDetailResponse.model_rebuild()
# in app/schemas/__init__.py once all schema modules are loaded.
