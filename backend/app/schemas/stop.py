from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StopResponse(BaseModel):
    id: str
    trip_id: str
    date: date
    location: str
    lat: Decimal | None
    lng: Decimal | None
    status: str
    region_code: str | None
    post_type: str
    caption: str | None
    # Populated only in GET /trips/:id; null/absent in list responses
    post: InstagramPostResponse | SubstackPostResponse | None = None  # type: ignore[name-defined]

    model_config = ConfigDict(from_attributes=True)


# Resolved after InstagramPostResponse and SubstackPostResponse are imported
# — call StopResponse.model_rebuild() in app/schemas/__init__.py.
