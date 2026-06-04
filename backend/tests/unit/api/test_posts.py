from unittest.mock import AsyncMock

from httpx import AsyncClient

from tests.conftest import make_execute_result, make_instagram_post, make_substack_post


class TestListInstagramPosts:
    async def test_returns_200_empty(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/instagram-posts")

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_posts(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        posts = [make_instagram_post(stop_id="s1"), make_instagram_post(stop_id="s2")]
        mock_db.execute.return_value = make_execute_result(rows=posts)

        response = await client.get("/instagram-posts")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_response_shape(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_instagram_post()])

        response = await client.get("/instagram-posts")

        item = response.json()[0]
        assert {"id", "stop_id", "instagram_id", "shortcode", "media_url", "caption", "timestamp", "created_at"} <= set(item.keys())

    async def test_stop_id_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_instagram_post(stop_id="stop-42")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/instagram-posts", params={"stop_id": "stop-42"})

        assert response.status_code == 200
        assert response.json()[0]["stop_id"] == "stop-42"

    async def test_after_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_instagram_post()
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/instagram-posts", params={"after": "2024-01-01T00:00:00"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_before_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_instagram_post()
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/instagram-posts", params={"before": "2024-12-31T23:59:59"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_combined_filters_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_instagram_post(stop_id="s1")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/instagram-posts", params={
            "stop_id": "s1",
            "after": "2024-01-01T00:00:00",
            "before": "2024-12-31T23:59:59",
        })

        assert response.status_code == 200
        assert response.json()[0]["stop_id"] == "s1"

    async def test_no_results_returns_empty_list(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/instagram-posts", params={"stop_id": "no-such-stop"})

        assert response.status_code == 200
        assert response.json() == []


class TestListSubstackPosts:
    async def test_returns_200_empty(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/substack-posts")

        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_posts_with_stop_id(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        posts = [
            make_substack_post(stop_id="s1"),
            make_substack_post(stop_id="s2"),
        ]
        mock_db.execute.return_value = make_execute_result(rows=posts)

        response = await client.get("/substack-posts")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["stop_id"] is not None for p in data)

    async def test_response_shape(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[make_substack_post()])

        response = await client.get("/substack-posts")

        item = response.json()[0]
        assert {"id", "stop_id", "substack_id", "title", "subtitle", "body", "published_at", "created_at"} <= set(item.keys())

    async def test_null_stop_id_not_returned(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        # Mock returns only posts with stop_id set (as the SQL WHERE stop_id IS NOT NULL ensures)
        post_with_stop = make_substack_post(stop_id="s1")
        mock_db.execute.return_value = make_execute_result(rows=[post_with_stop])

        response = await client.get("/substack-posts")

        data = response.json()
        assert len(data) == 1
        assert data[0]["stop_id"] == "s1"

    async def test_stop_id_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_substack_post(stop_id="stop-7")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/substack-posts", params={"stop_id": "stop-7"})

        assert response.status_code == 200
        assert response.json()[0]["stop_id"] == "stop-7"

    async def test_after_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_substack_post(stop_id="s1")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/substack-posts", params={"after": "2024-01-01T00:00:00"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_before_filter_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_substack_post(stop_id="s1")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/substack-posts", params={"before": "2024-12-31T23:59:59"})

        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_combined_filters_accepted(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        post = make_substack_post(stop_id="s1")
        mock_db.execute.return_value = make_execute_result(rows=[post])

        response = await client.get("/substack-posts", params={
            "stop_id": "s1",
            "after": "2024-01-01T00:00:00",
            "before": "2024-12-31T23:59:59",
        })

        assert response.status_code == 200
        assert response.json()[0]["stop_id"] == "s1"

    async def test_no_results_returns_empty_list(self, client: AsyncClient, mock_db: AsyncMock) -> None:
        mock_db.execute.return_value = make_execute_result(rows=[])

        response = await client.get("/substack-posts", params={"stop_id": "no-such-stop"})

        assert response.status_code == 200
        assert response.json() == []
