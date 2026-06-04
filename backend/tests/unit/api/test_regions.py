from unittest.mock import AsyncMock

from httpx import AsyncClient

from tests.conftest import make_execute_result, make_region


class TestListRegions:
    async def test_returns_200_empty(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/regions")

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_all_regions(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        regions = [make_region(iata_code="MDE"), make_region(iata_code="OAX")]
        mock_db.execute.return_value = make_execute_result(rows=regions)

        response = await client.get("/regions")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_response_shape(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_region()])

        response = await client.get("/regions")

        item = response.json()[0]
        assert {"iata_code", "name", "airport_name", "country", "lat", "lng"} <= set(item.keys())

    async def test_response_values(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_region(
            iata_code="MDE",
            name="Medellín",
            airport_name="José María Córdova International Airport",
            country="Colombia",
        )])

        response = await client.get("/regions")

        item = response.json()[0]
        assert item["iata_code"] == "MDE"
        assert item["name"] == "Medellín"
        assert item["airport_name"] == "José María Córdova International Airport"
        assert item["country"] == "Colombia"

    async def test_country_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        region = make_region(iata_code="MDE", country="Colombia")
        mock_db.execute.return_value = make_execute_result(rows=[region])

        response = await client.get("/regions", params={"country": "Colombia"})

        assert response.status_code == 200
        assert response.json()[0]["country"] == "Colombia"

    async def test_no_results_returns_empty_list(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/regions", params={"country": "Narnia"})

        assert response.status_code == 200
        assert response.json() == []

    async def test_no_auth_required(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_region()])

        response = await client.get("/regions")

        assert response.status_code == 200
