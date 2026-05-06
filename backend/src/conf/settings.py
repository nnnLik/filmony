import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings


class AppEnv(StrEnum):
    DEV = 'dev'
    PROD = 'prod'
    TEST = 'test'


class AppSettings(BaseSettings):
    TITLE: str = 'Filmony'
    DESCRIPTION: str = ''
    VERSION: str = '0.1.0'

    ENV: AppEnv = Field(default=AppEnv.DEV)
    RELOAD: bool = Field(True)

    HOST: str = Field('0.0.0.0')
    PORT: int = Field(8000)

    CORS_ALLOW_ORIGINS: list[str] = Field(default_factory=lambda: ['http://localhost:5173'])
    CORS_ALLOW_CREDENTIALS: bool = Field(True)
    CORS_ALLOW_METHODS: list[str] = Field(['*'])
    CORS_ALLOW_HEADERS: list[str] = Field(['*'])

    @property
    def worker_count(self) -> int:
        return os.cpu_count() * 2 + 1 if self.is_prod else 1

    @property
    def is_prod(self) -> bool:
        return self.ENV == AppEnv.PROD

    @property
    def is_test(self) -> bool:
        return self.ENV == AppEnv.TEST

    @property
    def openapi_config(self) -> dict[str, str | None]:
        return {
            'openapi_url': '/openapi.json',
            'docs_url': '/docs/swagger',
            'redoc_url': None,
        }


class DatabaseSettings(BaseSettings):
    url: str = Field(..., alias='DATABASE_URL')
    default_schema: str = Field(default='public', alias='DATABASE_SCHEMA')
    test_schema: str = Field(default='filmony_test', alias='DATABASE_TEST_SCHEMA')
    echo: bool = Field(False, alias='DATABASE_ECHO')

    @property
    def async_sqlalchemy_url(self) -> str:
        u = self.url.strip()
        if u.startswith('postgresql+asyncpg://'):
            return u
        if u.startswith('postgresql://'):
            return 'postgresql+asyncpg://' + u.removeprefix('postgresql://')
        return u


class TelegramAuthSettings(BaseSettings):
    bot_token: str = Field(..., alias='TG_APP_TOKEN')
    bot_username: str | None = Field('dev_filmony_bot', alias='TELEGRAM_BOT_USERNAME')


class AuthJwtSettings(BaseSettings):
    jwt_secret: str = Field('development-only-change-me-32chars!!', alias='AUTH_JWT_SECRET')
    session_cookie_name: str = Field('filmony_session', alias='SESSION_COOKIE_NAME')
    session_max_age_seconds: int = Field(604_800, alias='SESSION_MAX_AGE_SECONDS')


class ProfileSettings(BaseSettings):
    """Defaults for public profile movie-card lists (feature profile-and-public-profiles)."""

    page_size_default: int = Field(20, alias='PROFILE_CARDS_PAGE_SIZE_DEFAULT')
    page_size_max: int = Field(50, alias='PROFILE_CARDS_PAGE_SIZE_MAX')


@dataclass
class Settings:
    app: AppSettings
    database: DatabaseSettings
    telegram: TelegramAuthSettings
    auth_jwt: AuthJwtSettings
    profile: ProfileSettings

    @classmethod
    def build(cls) -> Self:
        return cls(
            app=AppSettings(),
            database=DatabaseSettings(),
            telegram=TelegramAuthSettings(),
            auth_jwt=AuthJwtSettings(),
            profile=ProfileSettings(),
        )


settings: Settings = Settings.build()
