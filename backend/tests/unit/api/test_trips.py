from datetime import date
from unittest.mock import AsyncMock

from httpx import AsyncClient

from tests.conftest import (
    make_execute_result,
    make_instagram_post,
    make_stop,
    make_substack_post,
    make_trip,
)


class TestListTrips:
    async def test_returns_200_empty(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/trips")

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_all_trips(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        trips = [
            make_trip(id="trip-a", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)),
            make_trip(id="trip-b", start_date=date(2023, 1, 1), end_date=date(2023, 12, 31)),
        ]
        mock_db.execute.return_value = make_execute_result(rows=trips)

        response = await client.get("/trips")

        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert ids == ["trip-a", "trip-b"]

    async def test_response_has_no_stops_field(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_trip()])

        response = await client.get("/trips")

        assert "stops" not in response.json()[0]

    async def test_response_shape(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_trip()])

        response = await client.get("/trips")

        item = response.json()[0]
        assert {"id", "title", "description", "start_date", "end_date", "created_at", "updated_at"} <= set(item.keys())

    async def test_status_active_keeps_active_trips(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        today = date.today()
        active = make_trip(id="active", start_date=date(today.year, 1, 1), end_date=date(today.year, 12, 31))
        completed = make_trip(id="completed", start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        mock_db.execute.return_value = make_execute_result(rows=[active, completed])

        response = await client.get("/trips", params={"status": "active"})

        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert "active" in ids
        assert "completed" not in ids

    async def test_status_completed_keeps_completed_trips(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        completed = make_trip(id="completed", start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        upcoming = make_trip(id="upcoming", start_date=date(2030, 1, 1), end_date=date(2030, 12, 31))
        mock_db.execute.return_value = make_execute_result(rows=[completed, upcoming])

        response = await client.get("/trips", params={"status": "completed"})

        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert "completed" in ids
        assert "upcoming" not in ids

    async def test_status_upcoming_keeps_upcoming_trips(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        upcoming = make_trip(id="upcoming", start_date=date(2030, 1, 1), end_date=date(2030, 12, 31))
        completed = make_trip(id="completed", start_date=date(2020, 1, 1), end_date=date(2020, 12, 31))
        mock_db.execute.return_value = make_execute_result(rows=[upcoming, completed])

        response = await client.get("/trips", params={"status": "upcoming"})

        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert "upcoming" in ids
        assert "completed" not in ids

    async def test_invalid_status_returns_422(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        response = await client.get("/trips", params={"status": "invalid"})

        assert response.status_code == 422
        assert response.json()["error"] == "Unprocessable Entity"


class TestGetTrip:
    async def test_unknown_id_returns_404(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(scalar=None)

        response = await client.get("/trips/does-not-exist")

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "Not Found"
        assert "does-not-exist" in body["detail"]

    async def test_returns_200_with_trip_fields(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        trip = make_trip(id="my-trip", stops=[])
        mock_db.execute.return_value = make_execute_result(scalar=trip)

        response = await client.get("/trips/my-trip")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "my-trip"
        assert "stops" in data

    async def test_instagram_stop_includes_post(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        ig_post = make_instagram_post(stop_id="stop-1", instagram_id="IG123")
        stop = make_stop(id="stop-1", post_type="instagram", instagram_post=ig_post, substack_post=None)
        trip = make_trip(stops=[stop])
        mock_db.execute.return_value = make_execute_result(scalar=trip)

        response = await client.get(f"/trips/{trip.id}")

        assert response.status_code == 200
        stop_data = response.json()["stops"][0]
        assert stop_data["post"] is not None
        assert stop_data["post"]["instagram_id"] == "IG123"

    async def test_substack_stop_includes_post(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        ss_post = make_substack_post(stop_id="stop-1", substack_id="https://example.substack.com/p/test")
        stop = make_stop(id="stop-1", post_type="substack", instagram_post=None, substack_post=ss_post)
        trip = make_trip(stops=[stop])
        mock_db.execute.return_value = make_execute_result(scalar=trip)

        response = await client.get(f"/trips/{trip.id}")

        assert response.status_code == 200
        stop_data = response.json()["stops"][0]
        assert stop_data["post"] is not None
        assert stop_data["post"]["substack_id"] == "https://example.substack.com/p/test"

    async def test_planned_stop_has_null_post(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(id="stop-1", post_type="planned", instagram_post=None, substack_post=None)
        trip = make_trip(stops=[stop])
        mock_db.execute.return_value = make_execute_result(scalar=trip)

        response = await client.get(f"/trips/{trip.id}")

        assert response.status_code == 200
        stop_data = response.json()["stops"][0]
        assert stop_data["post"] is None

    async def test_multiple_stops_all_types(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        ig_post = make_instagram_post(stop_id="s1")
        ss_post = make_substack_post(stop_id="s2")
        stops = [
            make_stop(id="s1", post_type="instagram", instagram_post=ig_post, substack_post=None),
            make_stop(id="s2", post_type="substack", instagram_post=None, substack_post=ss_post),
            make_stop(id="s3", post_type="planned", instagram_post=None, substack_post=None),
        ]
        trip = make_trip(stops=stops)
        mock_db.execute.return_value = make_execute_result(scalar=trip)

        response = await client.get(f"/trips/{trip.id}")

        assert response.status_code == 200
        result_stops = response.json()["stops"]
        assert len(result_stops) == 3
        assert result_stops[0]["post"] is not None
        assert result_stops[1]["post"] is not None
        assert result_stops[2]["post"] is None
