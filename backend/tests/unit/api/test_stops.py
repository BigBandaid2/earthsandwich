from datetime import date
from unittest.mock import AsyncMock

from httpx import AsyncClient

from tests.conftest import make_execute_result, make_stop


class TestListStops:
    async def test_returns_200_empty(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/stops")

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_all_stops(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stops = [make_stop(id="s1"), make_stop(id="s2")]
        mock_db.execute.return_value = make_execute_result(rows=stops)

        response = await client.get("/stops")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_response_shape(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_stop()])

        response = await client.get("/stops")

        item = response.json()[0]
        assert {"id", "trip_id", "date", "location", "lat", "lng", "status", "region_code", "post_type", "caption"} <= set(item.keys())

    async def test_no_post_data_in_list_response(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_stop()])

        response = await client.get("/stops")

        # post field is absent or null — no full post objects in list responses
        item = response.json()[0]
        assert item.get("post") is None

    # ── Filter tests ──────────────────────────────────────────────────────────

    async def test_trip_id_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(id="s1", trip_id="my-trip")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"trip_id": "my-trip"})

        assert response.status_code == 200
        assert response.json()[0]["trip_id"] == "my-trip"

    async def test_status_visited_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(status="visited")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"status": "visited"})

        assert response.status_code == 200
        assert response.json()[0]["status"] == "visited"

    async def test_status_planned_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(status="planned")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"status": "planned"})

        assert response.status_code == 200
        assert response.json()[0]["status"] == "planned"

    async def test_invalid_status_returns_422(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        response = await client.get("/stops", params={"status": "invalid"})

        assert response.status_code == 422
        assert response.json()["error"] == "Unprocessable Entity"

    async def test_region_code_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(region_code="LHR")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"region_code": "LHR"})

        assert response.status_code == 200
        assert response.json()[0]["region_code"] == "LHR"

    async def test_post_type_instagram_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(post_type="instagram")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"post_type": "instagram"})

        assert response.status_code == 200
        assert response.json()[0]["post_type"] == "instagram"

    async def test_post_type_substack_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(post_type="substack")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"post_type": "substack"})

        assert response.status_code == 200
        assert response.json()[0]["post_type"] == "substack"

    async def test_post_type_planned_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(post_type="planned")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"post_type": "planned"})

        assert response.status_code == 200
        assert response.json()[0]["post_type"] == "planned"

    async def test_invalid_post_type_returns_422(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        response = await client.get("/stops", params={"post_type": "video"})

        assert response.status_code == 422
        assert response.json()["error"] == "Unprocessable Entity"

    async def test_after_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(stop_date=date(2024, 8, 1))
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"after": "2024-07-01"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_before_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(stop_date=date(2024, 3, 1))
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={"before": "2024-06-01"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_combined_filters_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        stop = make_stop(trip_id="trip-1", status="visited", region_code="CDG", post_type="instagram")
        mock_db.execute.return_value = make_execute_result(rows=[stop])

        response = await client.get("/stops", params={
            "trip_id": "trip-1",
            "status": "visited",
            "region_code": "CDG",
            "post_type": "instagram",
            "after": "2024-01-01",
            "before": "2024-12-31",
        })

        assert response.status_code == 200
        item = response.json()[0]
        assert item["trip_id"] == "trip-1"
        assert item["status"] == "visited"
        assert item["region_code"] == "CDG"
        assert item["post_type"] == "instagram"

    async def test_no_results_returns_empty_list(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/stops", params={"trip_id": "no-such-trip"})

        assert response.status_code == 200
        assert response.json() == []
