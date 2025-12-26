import pytest

from main.render import RenderService


@pytest.mark.slow
@pytest.mark.integration
async def test_render_static_html_page():
    """測試渲染靜態 HTML 頁面 (使用 data: URL)"""
    service = RenderService(render_timeout=5)
    await service.start()

    html_content = (
        "<html><head><title>Test</title></head><body><h1>Hello World</h1></body></html>"
    )
    data_url = f"data:text/html,{html_content}"

    try:
        result = await service.render_page(data_url)

        assert "Hello World" in result
        assert "<html" in result
    finally:
        await service.stop()


@pytest.mark.slow
@pytest.mark.integration
async def test_render_javascript_page():
    """測試渲染包含 JavaScript 的頁面 (驗證 networkidle 等待 JS 執行)"""
    service = RenderService(render_timeout=10)
    await service.start()

    html_content = """
    <html>
    <head><title>JS Test</title></head>
    <body>
        <div id="content">Loading...</div>
        <script>
            setTimeout(function() {
                document.getElementById('content').textContent = 'JavaScript Executed';
            }, 100);
        </script>
    </body>
    </html>
    """
    data_url = f"data:text/html,{html_content}"

    try:
        result = await service.render_page(data_url)

        assert "JavaScript Executed" in result
    finally:
        await service.stop()


@pytest.mark.slow
@pytest.mark.integration
async def test_browser_not_initialized_raises_error():
    """測試瀏覽器未初始化時拋出 RuntimeError"""
    service = RenderService(render_timeout=5)

    with pytest.raises(RuntimeError, match="Browser not initialized"):
        await service.render_page("https://example.com")


@pytest.mark.slow
@pytest.mark.integration
async def test_render_after_stop_raises_error():
    """測試關閉後再渲染拋出錯誤"""
    service = RenderService(render_timeout=5)
    await service.start()
    await service.stop()

    with pytest.raises((RuntimeError, Exception)):
        await service.render_page("https://example.com")


@pytest.mark.slow
@pytest.mark.integration
async def test_normal_startup_and_shutdown():
    """測試正常啟動和關閉流程"""
    service = RenderService(render_timeout=5)

    assert service.browser is None

    await service.start()
    assert service.browser is not None

    await service.stop()


@pytest.mark.slow
@pytest.mark.integration
async def test_render_real_lightweight_page():
    """測試渲染真實的輕量級頁面"""
    service = RenderService(render_timeout=10)
    await service.start()

    try:
        result = await service.render_page("https://example.com")

        assert "<html" in result.lower()
        assert "example" in result.lower()
        assert len(result) > 100
    finally:
        await service.stop()


@pytest.mark.slow
@pytest.mark.integration
async def test_timeout_handling():
    """測試超時處理 (使用短 timeout)"""
    service = RenderService(render_timeout=1)
    await service.start()

    try:
        with pytest.raises((TimeoutError, Exception)):
            await service.render_page("https://httpstat.us/200?sleep=5000")
    finally:
        await service.stop()
