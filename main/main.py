from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, ORJSONResponse
from loguru import logger
from pydantic import HttpUrl

from .auth import verify_jwt_token
from .cache import SimpleCache
from .config import get_setting
from .dependencies import get_cache, get_render_service
from .helpers import normalize_url
from .render import RenderService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理應用生命週期：啟動/關閉資源"""
    # 啟動階段
    settings = get_setting()

    # 初始化渲染服務
    render_service = RenderService(render_timeout=settings.render_timeout)
    await render_service.start()
    app.state.render_service = render_service

    # 初始化快取
    cache = SimpleCache(
        ttl=settings.cache_ttl,
        max_entries=settings.cache_max_entries,
    )
    app.state.cache = cache

    yield  # 應用運行期間

    # 關閉階段
    await render_service.stop()


app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)


@app.get(
    "/render", response_class=HTMLResponse, dependencies=[Depends(verify_jwt_token)]
)
async def render_url(
    url: Annotated[HttpUrl, Query(description="URL to render")],
    cache: Annotated[SimpleCache, Depends(get_cache)],
    render_service: Annotated[RenderService, Depends(get_render_service)],
):
    """渲染指定 URL 的 JavaScript 內容（需要 JWT 認證）"""
    # 規範化 URL 用於快取和渲染
    url_str = normalize_url(url)

    # 檢查快取
    cached_html = cache.get(url_str)
    if cached_html:
        logger.info(f"Cache hit: {url_str}")
        return HTMLResponse(
            content=cached_html,
            headers={"X-Cache": "HIT", "X-Rendered-By": "Preplay"},
        )

    # 渲染頁面
    try:
        html = await render_service.render_page(url_str)
        cache.set(url_str, html)

        logger.info(f"Rendered and cached: {url_str}")
        return HTMLResponse(
            content=html, headers={"X-Cache": "MISS", "X-Rendered-By": "Preplay"}
        )

    except TimeoutError:
        logger.error(f"Timeout rendering: {url_str}")
        raise HTTPException(
            status_code=504,
            detail=f"Render timeout after {render_service.render_timeout}s",
        )
    except Exception as e:
        logger.error(f"Render error for {url_str}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during rendering"
        )


@app.get("/health")
async def health_check():
    """Kubernetes liveness probe - 基本健康檢查"""
    return {"status": "ok", "service": "preplay"}


@app.get("/readiness")
async def readiness_check(
    render_service: Annotated[RenderService, Depends(get_render_service)],
):
    """Kubernetes readiness probe - 檢查服務是否準備好"""
    if not render_service.browser:
        logger.warning("Readiness check failed: browser not initialized")
        raise HTTPException(
            status_code=503, detail="Service not ready: browser not initialized"
        )

    return {"status": "ready", "service": "preplay", "browser": "firefox"}
