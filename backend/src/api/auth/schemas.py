from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(
        validation_alias=AliasChoices("initData", "init_data"),
        serialization_alias="initData",
    )

    model_config = {"populate_by_name": True}


class UserResponse(BaseModel):
    id: UUID
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    language_code: str | None

    model_config = {"from_attributes": True}
