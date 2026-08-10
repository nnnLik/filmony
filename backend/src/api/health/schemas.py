from pydantic import BaseModel


class DependencyCheckResponse(BaseModel):
    status: str
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, DependencyCheckResponse]


class LivenessResponse(BaseModel):
    status: str
