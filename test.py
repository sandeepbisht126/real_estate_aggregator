import asyncio
from playwright.async_api import async_playwright

async def main():

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox"
            ]
        )

        page = await browser.new_page()

        await page.goto("https://example.com")

        print(await page.title())

        await page.wait_for_timeout(3000)

        await browser.close()

asyncio.run(main())