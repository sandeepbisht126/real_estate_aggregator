from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class ImmoScoutScraper:

    BASE_URL = "https://www.immobilienscout24.de"

    async def search(self, filters):

        search_url = (
            f"{self.BASE_URL}/Suche/"
            f"de/{filters.area}/wohnung-kaufen"
        )

        results = []

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            page = await browser.new_page()

            await page.goto(search_url)

            html = await page.content()

            soup = BeautifulSoup(html, "html.parser")

            listings = soup.select(".result-list-entry")

            for listing in listings:

                link = listing.select_one("a")

                if not link:
                    continue

                href = link.get("href")

                details = await self.parse_listing(
                    page,
                    href
                )

                if details:
                    results.append(details)

            await browser.close()

        return results

    async def parse_listing(self, page, url):

        await page.goto(url)

        html = await page.content()

        soup = BeautifulSoup(html, "html.parser")

        data = soup.get_text(" ", strip=True)

        return {
            "source": "immobilienscout24",
            "title": soup.title.text,
            "url": url,
            "energy_class": self.extract_energy(data),
            "hausgeld": self.extract_hausgeld(data),
        }

    def extract_energy(self, text):
        import re

        match = re.search(
            r"Energieeffizienzklasse\s+([A-H]\+?)",
            text
        )

        return match.group(1) if match else None

    def extract_hausgeld(self, text):
        import re

        match = re.search(r"Hausgeld\s+(\d+)", text)

        return float(match.group(1)) if match else None