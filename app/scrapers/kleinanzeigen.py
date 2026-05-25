import asyncio
import random
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


class KleinanzeigenScraper:

    BASE_URL = "https://www.kleinanzeigen.de"

    async def search(self, filters, max_pages=3):

        all_results = []

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = await browser.new_context(
                viewport={
                    "width": 1366,
                    "height": 768
                },
                locale="de-DE",
                user_agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            # Block heavy resources
            await context.route(
                "**/*",
                lambda route:
                route.abort()
                if route.request.resource_type
                in ["image", "media", "font"]
                else route.continue_()
            )

            page = await context.new_page()

            stealth = Stealth()

            await stealth.apply_stealth_async(page)

            for page_num in range(1, max_pages + 1):

                url = (
                    f"https://www.kleinanzeigen.de/"
                    f"s-wohnung-kaufen/"
                    f"berlin/"
                    f"preis:{filters.min_price}:{filters.max_price}/"
                    f"seite:{page_num}/"
                    f"c196l3331+"
                    f"wohnung_kaufen.qm_d:"
                    f"{filters.min_space}%2C{filters.max_space}+"
                    f"wohnung_kaufen.zimmer_d:"
                    f"{filters.min_rooms}%2C{filters.max_rooms}"
                )

                print(f"\nOpening: {url}")

                try:

                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=120000
                    )

                    await asyncio.sleep(
                        random.uniform(4, 7)
                    )

                    # Accept cookies

                    cookie_selectors = [

                        'button:has-text("Akzeptieren")',

                        'button:has-text("Alle akzeptieren")',

                        'button[id*="accept"]',

                        '[data-testid="gdpr-banner-accept"]'
                    ]

                    for selector in cookie_selectors:

                        try:

                            await page.locator(selector).click(
                                timeout=3000
                            )

                            print(
                                "Accepted cookies"
                            )

                            await asyncio.sleep(2)

                            break

                        except:
                            pass

                    # Human scrolling

                    await page.mouse.wheel(
                        0,
                        random.randint(1500, 3000)
                    )

                    await asyncio.sleep(
                        random.uniform(3, 6)
                    )

                    content = await page.content()

                    # Bot detection

                    if (
                        "access denied" in content.lower()
                        or "verify you are human"
                        in content.lower()
                    ):

                        print(
                            "Bot protection detected"
                        )

                        continue

                    soup = BeautifulSoup(
                        content,
                        "html.parser"
                    )

                    selectors = [
                        ".aditem",
                        "article",
                        '[data-testid="listing-card"]',
                        ".ad-listitem"
                    ]

                    ads = []

                    for selector in selectors:

                        ads = soup.select(selector)

                        if len(ads) > 0:

                            print(
                                f"Using selector: {selector}"
                            )

                            break

                    print(
                        f"Found {len(ads)} ads on page {page_num}"
                    )

                    if len(ads) == 0:

                        with open(
                            f"debug_page_{page_num}.html",
                            "w",
                            encoding="utf-8"
                        ) as f:

                            f.write(content)

                        continue

                    # Extract links

                    links = []

                    for ad in ads:

                        try:

                            link_el = ad.select_one("a")

                            if not link_el:
                                continue

                            href = link_el.get("href")

                            if not href:
                                continue

                            if not href.startswith("http"):

                                href = (
                                    self.BASE_URL
                                    + href
                                )

                            links.append(href)

                        except:
                            continue

                    # Remove duplicates

                    links = list(set(links))

                    print(
                        f"Extracted {len(links)} links"
                    )

                    # Sequential listing parsing

                    for link in links:

                        try:

                            result = await self.parse_listing(
                                page,
                                link
                            )

                            if result:

                                all_results.append(
                                    result
                                )

                            await asyncio.sleep(
                                random.uniform(4, 8)
                            )

                        except Exception as e:

                            print(
                                f"Failed listing {link}: {e}"
                            )

                    # Delay between pages

                    await asyncio.sleep(
                        random.uniform(10, 20)
                    )

                except Exception as e:

                    print(
                        f"Error on page {page_num}: {e}"
                    )

            await browser.close()

        return all_results

    async def parse_listing(
        self,
        page,
        url
    ):

        try:

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=120000
            )

            await asyncio.sleep(
                random.uniform(3, 6)
            )

            await page.mouse.wheel(
                0,
                random.randint(1000, 2500)
            )

            await asyncio.sleep(
                random.uniform(2, 5)
            )

            html = await page.content()

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            title_el = soup.select_one(
                "#viewad-title"
            )

            title = (
                title_el.get_text(
                    " ",
                    strip=True
                )
                if title_el else None
            )

            # FULL TEXT

            text = soup.get_text(
                " ",
                strip=True
            )

            # DETAILS

            details = {}

            detail_items = soup.select(
                "li.addetailslist--detail"
            )

            for item in detail_items:

                txt = item.get_text(
                    " ",
                    strip=True
                )

                print(f"DETAIL: {txt}")

                if "Wohnfläche" in txt:

                    details[
                        "living_space"
                    ] = self.extract_number(txt)

                elif "Zimmer" in txt:

                    details[
                        "rooms"
                    ] = self.extract_number(txt)

                elif "Schlafzimmer" in txt:

                    details[
                        "bedrooms"
                    ] = self.extract_number(txt)

                elif "Badezimmer" in txt:

                    details[
                        "bathrooms"
                    ] = self.extract_number(txt)

                elif "Etage" in txt:

                    floor_match = re.search(
                        r'Etage\s+(.+)',
                        txt
                    )

                    details["floor"] = (
                        floor_match.group(1)
                        if floor_match else None
                    )

                elif "Wohnungstyp" in txt:

                    details[
                        "property_type"
                    ] = self.extract_text_after_label(
                        txt
                    )

                elif "Baujahr" in txt:

                    year = self.extract_number(txt)

                    details["year_built"] = (
                        int(year)
                        if year else None
                    )

                elif "Hausgeld" in txt:

                    details[
                        "hausgeld"
                    ] = self.extract_number(txt)

                elif "Provision" in txt:

                    details[
                        "provision"
                    ] = self.extract_text_after_label(
                        txt
                    )

                elif "Verfügbar ab" in txt:

                    details[
                        "available_from"
                    ] = self.extract_text_after_label(
                        txt
                    )

            posted_date = None

            date_selectors = [

                '[data-testid="ad-date"]',

                '.viewad-subtitle',

                '.aditem-main--top'
            ]

            date_text = None

            for selector in date_selectors:

                try:

                    el = soup.select_one(selector)

                    if el:

                        txt = el.get_text(
                            " ",
                            strip=True
                        )

                        # Only keep reasonable text length
                        if len(txt) < 100:
                            date_text = txt
                            break

                except:
                    pass

            if date_text:

                print(
                    f"DATE TEXT: {date_text}"
                )

                now = datetime.now()

                if "Heute" in date_text:

                    time_match = re.search(
                        r'(\d{2}:\d{2})',
                        date_text
                    )

                    if time_match:

                        time_part = time_match.group(1)

                        posted_date = datetime.strptime(
                            f"{now.strftime('%Y-%m-%d')} {time_part}",
                            "%Y-%m-%d %H:%M"
                        )

                    else:

                        posted_date = now

                elif "Gestern" in date_text:

                    time_match = re.search(
                        r'(\d{2}:\d{2})',
                        date_text
                    )

                    yesterday = now - timedelta(days=1)

                    if time_match:

                        time_part = time_match.group(1)

                        posted_date = datetime.strptime(
                            f"{yesterday.strftime('%Y-%m-%d')} {time_part}",
                            "%Y-%m-%d %H:%M"
                        )

                    else:

                        posted_date = yesterday

                else:

                    date_match = re.search(
                        r'(\d{2}\.\d{2}\.\d{4})',
                        date_text
                    )

                    if date_match:

                        try:

                            posted_date = datetime.strptime(
                                date_match.group(1),
                                "%d.%m.%Y"
                            )

                        except:
                            pass

            property_obj = {

                "source": "kleinanzeigen",

                "title": title,

                "description": text,

                "price": self.extract_price(
                    text
                ),

                "living_space": details.get(
                    "living_space"
                ),

                "rooms": details.get(
                    "rooms"
                ),

                "bedrooms": details.get(
                    "bedrooms"
                ),

                "bathrooms": details.get(
                    "bathrooms"
                ),

                "floor": details.get(
                    "floor"
                ),

                "property_type": details.get(
                    "property_type"
                ),

                "year_built": details.get(
                    "year_built"
                ),

                "hausgeld": details.get(
                    "hausgeld"
                ),

                "provision": details.get(
                    "provision"
                ),

                "available_from": details.get(
                    "available_from"
                ),

                "balcony": self.extract_balcony(
                    text
                ),

                "city": self.extract_city(
                    text
                ),

                "area": self.extract_city(
                    text
                ),

                "energy_class": self.extract_energy_class(
                    text
                ),

                "posted_date": posted_date,

                "url": url
            }

            print(
                f"Parsed: {title}"
            )

            return property_obj

        except Exception as e:

            print(
                f"Listing parse error: {e}"
            )

            return None

    # -------------------------
    # HELPERS
    # -------------------------

    def extract_number(self, text):

        match = re.search(
            r"(\d+(?:[.,]\d+)?)",
            text
        )

        if match:

            return float(
                match.group(1)
                .replace(",", ".")
            )

        return None

    def extract_price(self, text):

        match = re.search(
            r'(\d{1,3}(?:\.\d{3})*)\s*€',
            text
        )

        if match:

            return float(
                match.group(1)
                .replace(".", "")
            )

        return None

    def extract_text_after_label(
        self,
        text
    ):

        parts = text.split(" ")

        if len(parts) > 1:

            return " ".join(parts[1:])

        return text

    def extract_balcony(self, text):

        keywords = [
            "Balkon",
            "Terrasse",
            "Loggia"
        ]

        text = text.lower()

        return any(
            keyword.lower() in text
            for keyword in keywords
        )

    def extract_energy_class(
        self,
        text
    ):

        match = re.search(
            r"Energieeffizienzklasse\s+([A-H]\+?)",
            text
        )

        if match:

            return match.group(1)

        return None

    def extract_city(
        self,
        text
    ):

        berlin_areas = [

            "Berlin",
            "Mitte",
            "Prenzlauer Berg",
            "Charlottenburg",
            "Kreuzberg",
            "Neukölln",
            "Adlershof"
        ]

        for area in berlin_areas:

            if area.lower() in text.lower():

                return area

        return "Berlin"