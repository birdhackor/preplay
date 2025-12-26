import asyncio
from typing import Optional

from loguru import logger
from playwright.async_api import Browser, async_playwright
from playwright.async_api import Error as PlaywrightError


class RenderService:
    """管理 Playwright 瀏覽器實例和頁面渲染"""

    def __init__(self, render_timeout: int = 30):
        """初始化渲染服務

        Args:
            render_timeout: 頁面渲染超時時間（秒）
        """
        self.render_timeout = render_timeout
        self.browser: Optional[Browser] = None
        self._playwright = None

    async def start(self) -> None:
        """啟動 Playwright 和瀏覽器實例"""
        logger.info("Starting Playwright browser...")
        try:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.firefox.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            logger.info("Playwright browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise

    async def stop(self) -> None:
        """關閉瀏覽器和 Playwright"""
        logger.info("Stopping Playwright browser...")
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
            if self._playwright:
                await self._playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.warning(f"Error during browser shutdown: {e}")

    async def render_page(self, url: str) -> str:
        """渲染指定 URL 並返回 HTML

        Args:
            url: 要渲染的完整 URL

        Returns:
            渲染後的 HTML 字串

        Raises:
            RuntimeError: 瀏覽器未初始化
            TimeoutError: 渲染超時
            PlaywrightError: Playwright 操作失敗
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Call start() first.")

        logger.info(f"Rendering URL: {url}")
        context = None
        page = None

        try:
            # 建立瀏覽器上下文（隔離環境）
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (compatible; PreplayBot/1.0)",
            )

            # 建立新頁面
            page = await context.new_page()

            # 導航到目標 URL，等待網路閒置
            await page.goto(
                url,
                wait_until="networkidle",
                timeout=self.render_timeout * 1000,  # 轉換為毫秒
            )

            # 提取完整 HTML
            html = await page.content()

            logger.info(f"Successfully rendered URL: {url} (size: {len(html)} bytes)")
            return html

        except asyncio.TimeoutError:
            logger.error(f"Timeout rendering URL: {url}")
            raise TimeoutError(f"Render timeout after {self.render_timeout}s")

        except PlaywrightError as e:
            logger.error(f"Playwright error rendering {url}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error rendering {url}: {e}")
            raise

        finally:
            # 清理資源
            if page:
                await page.close()
            if context:
                await context.close()
