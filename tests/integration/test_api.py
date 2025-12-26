import pytest


@pytest.mark.integration
def test_render_with_valid_token_returns_200(test_client_with_stub, valid_jwt_token):
    """測試使用有效 JWT token 的 /render 請求返回 200"""
    response = test_client_with_stub.get(
        "/render?url=https://example.com",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response.status_code == 200
    assert "<html>" in response.text
    assert "Stubbed content" in response.text
    assert response.headers["X-Rendered-By"] == "Preplay"
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


@pytest.mark.integration
def test_render_without_jwt_returns_401(test_client_with_stub):
    """測試缺少 JWT token 的 /render 請求返回 401 (HTTPBearer 自動處理)"""
    response = test_client_with_stub.get("/render?url=https://example.com")

    assert response.status_code == 401


@pytest.mark.integration
def test_render_with_invalid_jwt_returns_403(test_client_with_stub, invalid_jwt_token):
    """測試使用無效 JWT token 的 /render 請求返回 403"""
    response = test_client_with_stub.get(
        "/render?url=https://example.com",
        headers={"Authorization": f"Bearer {invalid_jwt_token}"},
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_render_with_expired_jwt_returns_403(test_client_with_stub, expired_jwt_token):
    """測試使用過期 JWT token 的 /render 請求返回 403"""
    response = test_client_with_stub.get(
        "/render?url=https://example.com",
        headers={"Authorization": f"Bearer {expired_jwt_token}"},
    )

    assert response.status_code == 403


@pytest.mark.integration
def test_render_with_invalid_url_returns_422(test_client_with_stub, valid_jwt_token):
    """測試無效 URL 格式返回 422"""
    response = test_client_with_stub.get(
        "/render?url=not-a-valid-url",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_render_first_request_cache_miss(test_client_with_stub, valid_jwt_token):
    """測試第一次請求返回 X-Cache: MISS"""
    response = test_client_with_stub.get(
        "/render?url=https://example.com/page1",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response.status_code == 200
    assert response.headers["X-Cache"] == "MISS"


@pytest.mark.integration
def test_render_second_request_cache_hit(test_client_with_stub, valid_jwt_token):
    """測試第二次請求相同 URL 返回 X-Cache: HIT"""
    url = "https://example.com/page2"

    response1 = test_client_with_stub.get(
        f"/render?url={url}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response1.headers["X-Cache"] == "MISS"

    response2 = test_client_with_stub.get(
        f"/render?url={url}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response2.status_code == 200
    assert response2.headers["X-Cache"] == "HIT"
    assert response1.text == response2.text


@pytest.mark.integration
def test_url_normalization_query_params(test_client_with_stub, valid_jwt_token):
    """測試 URL 正規化 - query 參數順序不同命中快取"""
    from urllib.parse import quote

    url1 = quote("https://example.com/page?a=1&b=2", safe="")
    url2 = quote("https://example.com/page?b=2&a=1", safe="")

    response1 = test_client_with_stub.get(
        f"/render?url={url1}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response1.headers["X-Cache"] == "MISS"

    response2 = test_client_with_stub.get(
        f"/render?url={url2}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response2.status_code == 200
    assert response2.headers["X-Cache"] == "HIT"


@pytest.mark.integration
def test_url_normalization_fragment(test_client_with_stub, valid_jwt_token):
    """測試 URL 正規化 - fragment 不同命中快取"""
    url1 = "https://example.com/page"
    url2 = "https://example.com/page#section"

    response1 = test_client_with_stub.get(
        f"/render?url={url1}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response1.headers["X-Cache"] == "MISS"

    response2 = test_client_with_stub.get(
        f"/render?url={url2}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )
    assert response2.status_code == 200
    assert response2.headers["X-Cache"] == "HIT"


@pytest.mark.integration
def test_health_endpoint_returns_200(test_client_with_stub):
    """測試 /health 端點返回 200"""
    response = test_client_with_stub.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "preplay"


@pytest.mark.integration
def test_readiness_browser_initialized_returns_200(test_client_with_stub):
    """測試瀏覽器已初始化時 /readiness 返回 200"""
    response = test_client_with_stub.get("/readiness")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["service"] == "preplay"
    assert response.json()["browser"] == "firefox"
