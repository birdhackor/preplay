from fastapi import Request

from .cache import SimpleCache
from .render import RenderService


def get_cache(request: Request) -> SimpleCache:
    """依賴注入：獲取快取實例"""
    return request.app.state.cache


def get_render_service(request: Request) -> RenderService:
    """依賴注入：獲取渲染服務實例"""
    return request.app.state.render_service
