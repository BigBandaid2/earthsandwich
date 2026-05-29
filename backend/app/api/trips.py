from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.stop import Stop
from app.models.trip import Trip
from app.schemas import (
    InstagramPostResponse,
    StopResponse,
    SubstackPostResponse,
    TripDetailResponse,
    TripResponse,
)

router = APIRouter(prefix="/trips", tags=["trips"])


def _trip_status(trip: Trip, today: date) -> str:
    if trip.start_date <= today <= trip.end_date:
        return "active"
    elif trip.end_date < today:
        return "completed"
    return "upcoming"


@router.get("", response_model=list[TripResponse])
async def list_trips(
    status: Literal["active", "completed", "upcoming"] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[TripResponse]:
    result = await db.execute(select(Trip).order_by(Trip.start_date.desc()))
    trips = result.scalars().all()

    today = date.today()
    if status is not None:
        trips = [t for t in trips if _trip_status(t, today) == status]

    return [TripResponse.model_validate(t) for t in trips]


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
) -> TripDetailResponse:
    result = await db.execute(
        select(Trip)
        .options(
            selectinload(Trip.stops).selectinload(Stop.instagram_post),
            selectinload(Trip.stops).selectinload(Stop.substack_post),
        )
        .where(Trip.id == trip_id)
    )
    trip = result.scalar_one_or_none()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trip with id '{trip_id}' does not exist.",
        )

    stops: list[StopResponse] = []
    for stop in trip.stops:
        if stop.post_type == "instagram" and stop.instagram_post is not None:
            post = InstagramPostResponse.model_validate(stop.instagram_post)
        elif stop.post_type == "substack" and stop.substack_post is not None:
            post = SubstackPostResponse.model_validate(stop.substack_post)
        else:
            post = None

        stops.append(StopResponse.model_validate(stop).model_copy(update={"post": post}))

    return TripDetailResponse(
        id=trip.id,
        title=trip.title,
        description=trip.description,
        start_date=trip.start_date,
        end_date=trip.end_date,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        stops=stops,
    )
