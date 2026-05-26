from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.stop import Stop
from app.schemas import StopResponse

router = APIRouter(prefix="/stops", tags=["stops"])


@router.get("", response_model=list[StopResponse])
async def list_stops(
    trip_id: str | None = Query(default=None),
    status: Literal["visited", "planned"] | None = Query(default=None),
    region_code: str | None = Query(default=None),
    post_type: Literal["instagram", "substack", "planned"] | None = Query(default=None),
    after: date | None = Query(default=None),
    before: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[StopResponse]:
    stmt = select(Stop)

    if trip_id is not None:
        stmt = stmt.where(Stop.trip_id == trip_id)
    if status is not None:
        stmt = stmt.where(Stop.status == status)
    if region_code is not None:
        stmt = stmt.where(Stop.region_code == region_code)
    if post_type is not None:
        stmt = stmt.where(Stop.post_type == post_type)
    if after is not None:
        stmt = stmt.where(Stop.date >= after)
    if before is not None:
        stmt = stmt.where(Stop.date <= before)

    stmt = stmt.order_by(Stop.date)

    result = await db.execute(stmt)
    stops = result.scalars().all()

    return [StopResponse.model_validate(s) for s in stops]
