import pytest


@pytest.mark.e2e
@pytest.mark.slow
def test_full_render_flow_with_real_playwright(test_client_real, valid_jwt_token):
    """測試完整流程: JWT 認證 → 渲染 → 快取 → 二次請求命中快取"""
    url = "https://example.com"

    response1 = test_client_real.get(
        f"/render?url={url}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response1.status_code == 200
    assert response1.headers["X-Cache"] == "MISS"
    assert response1.headers["X-Rendered-By"] == "Preplay"
    assert "Example Domain" in response1.text
    assert "<html" in response1.text.lower()

    response2 = test_client_real.get(
        f"/render?url={url}",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response2.status_code == 200
    assert response2.headers["X-Cache"] == "HIT"
    assert response2.headers["X-Rendered-By"] == "Preplay"
    assert response1.text == response2.text


@pytest.mark.e2e
@pytest.mark.slow
def test_verify_html_content(test_client_real, valid_jwt_token):
    """測試驗證 HTML 包含預期內容"""
    response = test_client_real.get(
        "/render?url=https://example.com",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response.status_code == 200
    content = response.text.lower()

    assert "<html" in content
    assert "</html>" in content
    assert "example domain" in content


@pytest.mark.e2e
@pytest.mark.slow
def test_verify_response_headers(test_client_real, valid_jwt_token):
    """測試驗證所有響應 headers"""
    response = test_client_real.get(
        "/render?url=https://example.com",
        headers={"Authorization": f"Bearer {valid_jwt_token}"},
    )

    assert response.status_code == 200
    assert "X-Cache" in response.headers
    assert response.headers["X-Rendered-By"] == "Preplay"
    assert "text/html" in response.headers["Content-Type"]
