from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.instagram_post import InstagramPost
from app.models.substack_post import SubstackPost
from app.schemas import InstagramPostResponse, SubstackPostResponse

router = APIRouter(tags=["posts"])


@router.get("/instagram-posts", response_model=list[InstagramPostResponse])
async def list_instagram_posts(
    stop_id: str | None = Query(default=None),
    after: datetime | None = Query(default=None),
    before: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[InstagramPostResponse]:
    stmt = select(InstagramPost)

    if stop_id is not None:
        stmt = stmt.where(InstagramPost.stop_id == stop_id)
    if after is not None:
        stmt = stmt.where(InstagramPost.timestamp >= after)
    if before is not None:
        stmt = stmt.where(InstagramPost.timestamp <= before)

    stmt = stmt.order_by(InstagramPost.timestamp)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    return [InstagramPostResponse.model_validate(p) for p in posts]


@router.get("/substack-posts", response_model=list[SubstackPostResponse])
async def list_substack_posts(
    stop_id: str | None = Query(default=None),
    after: datetime | None = Query(default=None),
    before: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[SubstackPostResponse]:
    stmt = select(SubstackPost).where(SubstackPost.stop_id.is_not(None))

    if stop_id is not None:
        stmt = stmt.where(SubstackPost.stop_id == stop_id)
    if after is not None:
        stmt = stmt.where(SubstackPost.published_at >= after)
    if before is not None:
        stmt = stmt.where(SubstackPost.published_at <= before)

    stmt = stmt.order_by(SubstackPost.published_at)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    return [SubstackPostResponse.model_validate(p) for p in posts]
