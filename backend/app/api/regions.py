from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.region import Region
from app.schemas.region import RegionResponse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=list[RegionResponse])
async def list_regions(
    country: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[RegionResponse]:
    stmt = select(Region)

    if country is not None:
        stmt = stmt.where(Region.country == country)

    result = await db.execute(stmt)
    regions = result.scalars().all()

    return [RegionResponse.model_validate(r) for r in regions]
