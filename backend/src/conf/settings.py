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

    CORS_ALLOW_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            'http://localhost:5173',
            'http://localhost:5176',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:5176',
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(True)
    CORS_ALLOW_METHODS: list[str] = Field(['*'])
    CORS_ALLOW_HEADERS: list[str] = Field(['*'])

    @property
    def worker_count(self) -> int:
        return 1

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
    test_url: str | None = Field(default=None, alias='DATABASE_TEST_URL')
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


class KinopoiskSettings(BaseSettings):
    api_key: str = Field(..., alias='KINOPOISK_API_KEY')
    base_url: str = Field(..., alias='KINOPOISK_API_BASE_URL')
    enrich_director_id: bool = Field(True, alias='ENRICH_KP_DIRECTOR_ID')


class TmdbSettings(BaseSettings):
    api_key: str = Field('development-placeholder', alias='TMDB_API_KEY')
    read_access_token: str | None = Field(None, alias='TMDB_API_READ_ACCESS_TOKEN')
    base_url: str = Field('https://api.themoviedb.org/3', alias='TMDB_API_BASE_URL')
    image_base_url: str = Field('https://image.tmdb.org/t/p/w500', alias='TMDB_IMAGE_BASE_URL')
    language: str = Field('ru-RU', alias='TMDB_LANGUAGE')


class RawgSettings(BaseSettings):
    api_key: str = Field(..., alias='RAWG_API_KEY')
    base_url: str = Field('https://api.rawg.io/api', alias='RAWG_API_BASE_URL')


class ReactionMediaSettings(BaseSettings):
    public_base_url: str = Field('', alias='REACTION_MEDIA_PUBLIC_BASE_URL')
    rustfs_internal_base_url: str = Field('', alias='RUSTFS_INTERNAL_BASE_URL')
    rustfs_bucket: str = Field('filmony-reactions', alias='RUSTFS_BUCKET')
    rustfs_access_key: str = Field('', alias='RUSTFS_ACCESS_KEY')
    rustfs_secret_key: str = Field('', alias='RUSTFS_SECRET_KEY')


class CelerySettings(BaseSettings):
    broker_url: str = Field(..., alias='CELERY_BROKER_URL')
    result_backend: str | None = Field(None, alias='CELERY_RESULT_BACKEND')


class CatalogCacheSettings(BaseSettings):
    """Redis-backed catalog search/resolve cache (falls back to ``CELERY_BROKER_URL`` when Redis)."""

    redis_url: str | None = Field(None, alias='CATALOG_CACHE_REDIS_URL')
    search_ttl_seconds: int = Field(45, alias='CATALOG_CACHE_SEARCH_TTL_SECONDS')
    resolve_ttl_seconds: int = Field(60, alias='CATALOG_CACHE_RESOLVE_TTL_SECONDS')


class PlaybackSettings(BaseSettings):
    enabled: bool = Field(True, alias='PLAYBACK_ENABLED')
    pleer_video_api_base_url: str = Field('https://pleer.video', alias='PLEER_VIDEO_API_BASE_URL')
    cache_ttl_seconds: int = Field(600, alias='PLAYBACK_CACHE_TTL_SECONDS')


class WatchPartySettings(BaseSettings):
    hard_max_members: int = Field(64, alias='WATCH_PARTY_HARD_MAX_MEMBERS')
    max_active_per_user: int = Field(1, alias='WATCH_PARTY_MAX_ACTIVE_PER_USER')
    ttl_hours: int = Field(12, alias='WATCH_PARTY_TTL_HOURS')
    sse_ping_seconds: int = Field(25, alias='WATCH_PARTY_SSE_PING_SECONDS')
    public_app_base_url: str = Field('http://localhost:5173', alias='PUBLIC_APP_BASE_URL')
    redis_url: str | None = Field(None, alias='WATCH_PARTY_REDIS_URL')
    chat_max_messages: int = Field(200, alias='WATCH_PARTY_CHAT_MAX_MESSAGES')
    chat_page_size: int = Field(50, alias='WATCH_PARTY_CHAT_PAGE_SIZE')
    seek_rate_limit: int = Field(10, alias='WATCH_PARTY_SEEK_RATE_LIMIT')
    heartbeat_interval_seconds: int = Field(30, alias='WATCH_PARTY_HEARTBEAT_INTERVAL_SECONDS')
    missed_heartbeats_away: int = Field(3, alias='WATCH_PARTY_MISSED_HEARTBEATS_AWAY')
    missed_heartbeats_left: int = Field(20, alias='WATCH_PARTY_MISSED_HEARTBEATS_LEFT')
    typing_ttl_seconds: int = Field(3, alias='WATCH_PARTY_TYPING_TTL_SECONDS')


@dataclass
class Settings:
    app: AppSettings
    database: DatabaseSettings
    telegram: TelegramAuthSettings
    auth_jwt: AuthJwtSettings
    kinopoisk: KinopoiskSettings
    tmdb: TmdbSettings
    rawg: RawgSettings
    reaction_media: ReactionMediaSettings
    celery: CelerySettings
    catalog_cache: CatalogCacheSettings
    playback: PlaybackSettings
    watch_party: WatchPartySettings

    @classmethod
    def build(cls) -> Self:
        return cls(
            app=AppSettings(),
            database=DatabaseSettings(),
            telegram=TelegramAuthSettings(),
            auth_jwt=AuthJwtSettings(),
            kinopoisk=KinopoiskSettings(),
            tmdb=TmdbSettings(),
            rawg=RawgSettings(),
            reaction_media=ReactionMediaSettings(),
            celery=CelerySettings(),
            catalog_cache=CatalogCacheSettings(),
            playback=PlaybackSettings(),
            watch_party=WatchPartySettings(),
        )


settings: Settings = Settings.build()
