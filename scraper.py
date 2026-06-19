import asyncio
import json
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page
from playwright_stealth import Stealth


class TikTokScraper:
    def __init__(
        self,
        cookie_file: Optional[Path] = None,
        proxy: Optional[dict] = None,
        stealth: bool = False,
        headless: bool = True,
    ):
        self.cookie_file = cookie_file
        self.proxy = proxy       # e.g. {"server": "http://host:port", "username": "...", "password": "..."}
        self.stealth = stealth
        self.headless = headless

    async def _load_cookies(self, context: BrowserContext) -> None:
        if not self.cookie_file or not self.cookie_file.exists():
            return
        cookies = json.loads(self.cookie_file.read_text())
        await context.add_cookies(cookies)

    async def _new_context(self, playwright) -> BrowserContext:
        launch_kwargs = {"headless": self.headless}
        if self.proxy:
            launch_kwargs["proxy"] = self.proxy

        browser = await playwright.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        await self._load_cookies(context)
        return context

    async def scrape(self, url: str) -> dict:
        async with async_playwright() as p:
            context = await self._new_context(p)
            page: Page = await context.new_page()

            if self.stealth:
                await Stealth().apply_stealth_async(page)

            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Wait for the rehydration script tag to be present
            await page.wait_for_selector(
                "script#__UNIVERSAL_DATA_FOR_REHYDRATION__",
                state="attached",
                timeout=15_000,
            )

            raw = await page.evaluate(
                "document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__').textContent"
            )

            await context.close()

        return json.loads(raw)


async def main():
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.tiktok.com/@tiktok/video/7106594312292177194"

    scraper = TikTokScraper(
        # Uncomment to use cookies:
        # cookie_file=Path("cookies.json"),

        # Uncomment to use a proxy:
        # proxy={"server": "http://host:port"},

        # Uncomment to enable stealth mode:
        # stealth=True,

        headless=True,
    )

    from extractor import extract_video

    raw = await scraper.scrape(url)
    video = extract_video(raw)
    print(json.dumps(video, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
