import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


# ── DB result helper ──────────────────────────────────────────────────────────

def make_execute_result(
    rows: list | None = None,
    scalar=None,
) -> MagicMock:
    """Build a mock SQLAlchemy AsyncResult supporting .scalars().all() and .scalar_one_or_none()."""
    result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows if rows is not None else []
    result.scalars.return_value = scalars_mock
    result.scalar_one_or_none.return_value = scalar
    return result


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_db() -> AsyncMock:
    """Async mock SQLAlchemy session; configure execute return_value per test."""
    session = AsyncMock()
    session.execute.return_value = make_execute_result()
    return session


@pytest_asyncio.fixture
async def client(mock_db: AsyncMock) -> AsyncGenerator[tuple[AsyncClient, AsyncMock], None]:
    """httpx AsyncClient with get_db overridden to yield mock_db.

    Yields (client, mock_db) so tests can configure mock_db before requests.
    """

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, mock_db
    app.dependency_overrides.pop(get_db, None)


# ── ORM object factories ──────────────────────────────────────────────────────

def make_trip(
    id: str = "test-trip-2024",
    title: str = "Test Trip",
    description: str = "A test trip description.",
    start_date: date = date(2024, 1, 1),
    end_date: date = date(2024, 12, 31),
    created_at: datetime = datetime(2024, 1, 1, 0, 0, 0),
    updated_at: datetime = datetime(2024, 1, 1, 0, 0, 0),
    stops: list | None = None,
) -> MagicMock:
    trip = MagicMock()
    trip.id = id
    trip.title = title
    trip.description = description
    trip.start_date = start_date
    trip.end_date = end_date
    trip.created_at = created_at
    trip.updated_at = updated_at
    trip.stops = stops if stops is not None else []
    return trip


def make_stop(
    id: str = "stop-1",
    trip_id: str = "test-trip-2024",
    stop_date: date = date(2024, 6, 15),
    location: str = "Paris, France",
    lat: Decimal = Decimal("48.8566"),
    lng: Decimal = Decimal("2.3522"),
    status: str = "visited",
    region_code: str = "CDG",
    post_type: str = "instagram",
    caption: str | None = None,
    instagram_post=None,
    substack_post=None,
) -> MagicMock:
    stop = MagicMock()
    stop.id = id
    stop.trip_id = trip_id
    stop.date = stop_date
    stop.location = location
    stop.lat = lat
    stop.lng = lng
    stop.status = status
    stop.region_code = region_code
    stop.post_type = post_type
    stop.caption = caption
    stop.instagram_post = instagram_post
    stop.substack_post = substack_post
    stop.created_at = datetime(2024, 6, 15, 0, 0, 0)
    return stop


def make_instagram_post(
    id: uuid.UUID | None = None,
    stop_id: str = "stop-1",
    instagram_id: str = "18001223977200451",
    shortcode: str = "BxZ6Y-Zh1jC",
    media_url: str = "/media/stop-1.jpg",
    caption: str = "A great photo.",
    timestamp: datetime = datetime(2024, 6, 15, 12, 0, 0),
    created_at: datetime = datetime(2024, 6, 15, 0, 0, 0),
) -> MagicMock:
    post = MagicMock()
    post.id = id if id is not None else uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    post.stop_id = stop_id
    post.instagram_id = instagram_id
    post.shortcode = shortcode
    post.media_url = media_url
    post.caption = caption
    post.timestamp = timestamp
    post.created_at = created_at
    return post


def make_substack_post(
    id: uuid.UUID | None = None,
    stop_id: str | None = "stop-1",
    substack_id: str = "https://example.substack.com/p/test-post",
    title: str = "Test Article",
    subtitle: str | None = "A brief subtitle.",
    body: str = "Full article body text.",
    published_at: datetime = datetime(2024, 6, 15, 12, 0, 0),
    created_at: datetime = datetime(2024, 6, 15, 0, 0, 0),
) -> MagicMock:
    post = MagicMock()
    post.id = id if id is not None else uuid.UUID("550e8400-e29b-41d4-a716-446655440001")
    post.stop_id = stop_id
    post.substack_id = substack_id
    post.title = title
    post.subtitle = subtitle
    post.body = body
    post.published_at = published_at
    post.created_at = created_at
    return post
