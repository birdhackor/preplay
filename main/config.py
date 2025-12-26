from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_keys: dict[str, bytes]
    render_timeout: int = 30
    cache_ttl: int = 86400
    cache_max_entries: int = 50


@lru_cache
def get_setting():
    return Settings()  # type: ignore


async def async_get_setting():
    return Settings()  # type: ignore
