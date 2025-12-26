import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main.cache import SimpleCache
from main.dependencies import get_cache, get_render_service
from main.render import RenderService


@pytest.fixture(scope="function", autouse=True)
def test_env(monkeypatch):
    """設定測試環境變數"""
    monkeypatch.setenv("JWT_KEYS", '{"default": "testsecret"}')
    monkeypatch.setenv("CACHE_TTL", "60")
    monkeypatch.setenv("CACHE_MAX_ENTRIES", "10")
    monkeypatch.setenv("RENDER_TIMEOUT", "5")


@pytest.fixture
def valid_jwt_token():
    """生成有效的測試 JWT token"""
    return jwt.encode({"sub": "testuser"}, b"testsecret", algorithm="HS256")


@pytest.fixture
def expired_jwt_token():
    """生成過期的 JWT token"""
    return jwt.encode(
        {"sub": "testuser", "exp": int(time.time()) - 3600},
        b"testsecret",
        algorithm="HS256",
    )


@pytest.fixture
def invalid_jwt_token():
    """無效簽名的 JWT token"""
    return jwt.encode({"sub": "testuser"}, b"wrongsecret", algorithm="HS256")


@pytest.fixture
def cache():
    """創建測試快取實例"""
    return SimpleCache(ttl=60, max_entries=10)


class StubRenderService:
    """Stub render service 用於快速 API 測試"""

    def __init__(self, render_timeout: int = 30):
        self.render_timeout = render_timeout
        self._browser = True
        self._should_timeout = False
        self._should_error = False

    async def start(self):
        pass

    async def stop(self):
        pass

    async def render_page(self, url: str) -> str:
        if self._should_timeout:
            raise TimeoutError(f"Timeout while rendering {url}")
        if self._should_error:
            raise Exception(f"Error while rendering {url}")
        return f"<html><body>Stubbed content for {url}</body></html>"

    @property
    def browser(self):
        return self._browser

    def set_browser_state(self, initialized: bool):
        """用於測試 readiness 端點"""
        self._browser = True if initialized else None

    def enable_timeout(self):
        """模擬渲染超時"""
        self._should_timeout = True

    def enable_error(self):
        """模擬渲染錯誤"""
        self._should_error = True


@pytest.fixture
def stub_render_service():
    """創建 stub render service 實例"""
    return StubRenderService()


@pytest.fixture
def test_client_with_stub(test_env):
    """使用 stubbed RenderService 的測試客戶端"""
    from contextlib import asynccontextmanager
    from typing import AsyncGenerator

    from fastapi import Depends, FastAPI, HTTPException, Query
    from fastapi.responses import HTMLResponse
    from pydantic import HttpUrl

    @asynccontextmanager
    async def stub_lifespan(app: FastAPI) -> AsyncGenerator:
        stub_service = StubRenderService()
        stub_cache = SimpleCache(ttl=60, max_entries=10)

        app.state.render_service = stub_service
        app.state.cache = stub_cache

        yield

    from main.auth import verify_jwt_token
    from main.helpers import normalize_url

    app = FastAPI(lifespan=stub_lifespan)

    @app.get(
        "/render", response_class=HTMLResponse, dependencies=[Depends(verify_jwt_token)]
    )
    async def render_url(
        url: HttpUrl = Query(...),
        cache: SimpleCache = Depends(get_cache),
        render_service: RenderService = Depends(get_render_service),
    ):
        url_str = normalize_url(url)
        cached_html = cache.get(url_str)
        if cached_html:
            return HTMLResponse(
                content=cached_html,
                headers={"X-Cache": "HIT", "X-Rendered-By": "Preplay"},
            )
        try:
            html = await render_service.render_page(url_str)
            cache.set(url_str, html)
            return HTMLResponse(
                content=html, headers={"X-Cache": "MISS", "X-Rendered-By": "Preplay"}
            )
        except TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"Render timeout after {render_service.render_timeout}s",
            )
        except Exception:
            raise HTTPException(
                status_code=500, detail="Internal server error during rendering"
            )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "preplay"}

    @app.get("/readiness")
    async def readiness_check(
        render_service: RenderService = Depends(get_render_service),
    ):
        if not render_service.browser:
            raise HTTPException(
                status_code=503, detail="Service not ready: browser not initialized"
            )
        return {"status": "ready", "service": "preplay", "browser": "firefox"}

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_html():
    """模擬渲染的 HTML"""
    return "<html><body><h1>Test Page</h1><p>This is a test page with JavaScript.</p></body></html>"


@pytest.fixture(scope="module")
async def real_render_service():
    """創建真實的 Playwright RenderService (用於慢速測試)"""
    service = RenderService(render_timeout=5)
    await service.start()
    yield service
    await service.stop()


@pytest.fixture(scope="function")
def test_client_real(test_env):
    """使用真實 Playwright 的測試客戶端 (用於 E2E 測試)"""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        render_service = RenderService(render_timeout=5)
        cache = SimpleCache(ttl=60, max_entries=10)

        app.state.render_service = render_service
        app.state.cache = cache

        await render_service.start()

        yield

        await render_service.stop()

    from main.main import app as original_app

    app = FastAPI(lifespan=lifespan)
    app.include_router(original_app.router)

    with TestClient(app) as client:
        yield client
