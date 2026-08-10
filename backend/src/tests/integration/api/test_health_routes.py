from httpx import AsyncClient


async def test_health_liveness(async_client: AsyncClient) -> None:
    response = await async_client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


async def test_health_ready_ok(async_client: AsyncClient) -> None:
    response = await async_client.get('/health/ready')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['checks']['postgres']['status'] == 'ok'
    assert payload['checks']['redis']['status'] == 'ok'
