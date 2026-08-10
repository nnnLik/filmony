from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.health.schemas import LivenessResponse, ReadinessResponse
from services.health.check_backend_readiness import (
    CheckBackendReadinessService,
    ReadinessResult,
)

router = APIRouter(tags=['health'])


def _readiness_payload(result: ReadinessResult) -> dict[str, object]:
    checks: dict[str, dict[str, str]] = {}
    for name, check in result.checks.items():
        entry: dict[str, str] = {'status': check.status}
        if check.detail is not None:
            entry['detail'] = check.detail
        checks[name] = entry
    return {'status': result.status, 'checks': checks}


@router.get('/health', response_model=LivenessResponse)
def health_liveness() -> dict[str, str]:
    return {'status': 'ok'}


@router.get(
    '/health/ready',
    response_model=ReadinessResponse,
    response_model_exclude_none=True,
)
async def health_readiness() -> JSONResponse | dict[str, object]:
    result = await CheckBackendReadinessService.build().execute()
    payload = _readiness_payload(result)
    if not result.is_ready:
        return JSONResponse(status_code=503, content=payload)
    return payload
