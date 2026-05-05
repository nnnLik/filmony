from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramWebAppUser:
    """User payload parsed from verified initData (Telegram Web App)."""

    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    language_code: str | None
