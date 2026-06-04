from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class RegionResponse(BaseModel):
    iata_code: str
    name: str
    airport_name: str
    country: str
    lat: float
    lng: float

    model_config = ConfigDict(from_attributes=True)
