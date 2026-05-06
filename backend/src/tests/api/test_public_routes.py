from httpx import AsyncClient


async def test_root(async_client: AsyncClient) -> None:
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


async def test_api_hello(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Filmony backend"}
