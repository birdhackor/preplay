from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_keys: dict[str, bytes]


@lru_cache
def get_setting():
    return Settings()  # type: ignore


async def async_get_setting():
    return Settings()  # type: ignore
