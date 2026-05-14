from .rawg_openapi_dto import (
    RawgEsrbRatingDTO,
    RawgGameDTO,
    RawgGameDtoParseError,
    RawgGamePlatformItemDTO,
    RawgGamePlatformMetacriticDTO,
    RawgGamePlatformRefDTO,
    RawgGamePlatformRequirementsDTO,
    RawgGameSingleDTO,
    RawgGamesListQueryParams,
    RawgGamesListResponseDTO,
)
from .rawg_provider_transport import RawgEndpointEnum, RawgProviderTransport

RawgProviderTransportError = RawgProviderTransport.RawgProviderTransportError

RawgGameSummaryDTO = RawgGameDTO
RawgGameDetailDTO = RawgGameSingleDTO
RawgGameSearchResultDTO = RawgGamesListResponseDTO

__all__ = [
    'RawgEndpointEnum',
    'RawgEsrbRatingDTO',
    'RawgGameDTO',
    'RawgGameDetailDTO',
    'RawgGameDtoParseError',
    'RawgGamePlatformItemDTO',
    'RawgGamePlatformMetacriticDTO',
    'RawgGamePlatformRefDTO',
    'RawgGamePlatformRequirementsDTO',
    'RawgGameSearchResultDTO',
    'RawgGameSingleDTO',
    'RawgGameSummaryDTO',
    'RawgGamesListQueryParams',
    'RawgGamesListResponseDTO',
    'RawgProviderTransport',
    'RawgProviderTransportError',
]
