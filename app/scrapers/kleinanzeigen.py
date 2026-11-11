import asyncio
import random
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

INVESTMENT_KEYWORDS = [
    "kapitalanlage",
    "renditeobjekt",
    "anlageobjekt",
    "anlegerwohnung"
]

# Floor types to exclude (more specific patterns)
# EXCLUDED_FLOOR_TYPES = [
#     "erdgeschoss",
#     "dachgeschoss",
#     "souterrain"
# ]
EXCLUDED_FLOOR_TYPES = []

class KleinanzeigenScraper:
    BASE_URL = "https://www.kleinanzeigen.de"

    def is_investment_property(self, text, title):
        """Check if property is an investment property (more precise matching)"""
        text = text.lower() + " " + title.lower()
        
        # Check for investment keywords with word boundaries
        for keyword in INVESTMENT_KEYWORDS:
            # Match as whole word or phrase
            if f" {keyword} " in text or text.startswith(keyword + " ") or text.endswith(" " + keyword):
                print(f"[DEBUG] Investment keyword found: '{keyword}'")
                return True
        
        return False
    
    def is_excluded_floor(self, text, title):
        """Check if property is on excluded floor (ground floor, attic, etc.) - more precise"""
        text = text.lower() + " " + title.lower()
        
        # Check for floor types with word boundaries
        for floor_type in EXCLUDED_FLOOR_TYPES:
            # Match as whole word
            if f" {floor_type} " in text or text.startswith(floor_type + " ") or text.endswith(" " + floor_type):
                print(f"[DEBUG] Excluded floor found: '{floor_type}'")
                return True
        
        return False

    def normalize_property_type(self, property_type):

        if not property_type:
            return ""

        p = property_type.lower()

        mapping = {

            # Apartments
            "etagenwohnung": "Apartment",
            "erdgeschosswohnung": "Ground Floor Apartment",
            "dachgeschosswohnung": "Top Floor Apartment",
            "maisonette": "Maisonette Apartment",
            "penthouse": "Penthouse",
            "souterrainwohnung": "Basement Apartment",
            "loft": "Loft",
            "studio": "Studio Apartment",

            # Houses
            "einfamilienhaus": "Detached House",
            "mehrfamilienhaus": "Multi-family House",
            "reihenhaus": "Terraced House",
            "reihenendhaus": "End-of-Terrace House",
            "doppelhaushälfte": "Semi-detached House",
            "villa": "Villa",
            "bungalow": "Bungalow",

            # Special
            "bauernhaus": "Farmhouse",
            "landhaus": "Country House",
            "schloss": "Castle",
            "ferienhaus": "Holiday House",

            # Generic
            "haus": "House",
            "wohnung": "Apartment"
        }

        for german, english in mapping.items():

            if german in p:
                return english

        return property_type

    async def search(self, filters, max_pages, max_results=None, fast_mode=False, progress_callback=None):

        all_results = []
        
        if max_results is None:
            max_results = 9999  # No limit if not specified
        
        import time
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0, f"Starting scrape for {max_results} properties...")

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=True,
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

            empty_page_count = 0

            for page_num in range(1, max_pages + 1):

                url = (
                    f"https://www.kleinanzeigen.de/"
                    f"s-wohnung-kaufen/"
                    f"berlin/"
                    f"sortierung:neuste/"
                    f"preis:{filters.min_price}:{filters.max_price}/"
                    f"seite:{page_num}/"
                    f"c196l3331+"
                    f"wohnung_kaufen.qm_d:"
                    f"{filters.min_space}%2C{filters.max_space}+"
                    f"wohnung_kaufen.zimmer_d:"
                    f"{filters.min_rooms}%2C{filters.max_rooms}"
                )

                print(f"\nOpening: {url}")
                
                if progress_callback:
                    elapsed = time.time() - start_time
                    if elapsed > 5:  # Only show estimate after 5 seconds
                        # Estimate based on current progress
                        current_progress = 0.1 + (page_num / max_pages) * 0.2
                        estimated_total = elapsed / current_progress if current_progress > 0 else 0
                        remaining = estimated_total - elapsed
                        progress_callback(
                            current_progress,
                            f"Scanning page {page_num}/{max_pages}... (ETA: {int(remaining)}s)"
                        )
                    else:
                        progress_callback(
                            0.1 + (page_num / max_pages) * 0.2,
                            f"Scanning page {page_num}/{max_pages}..."
                        )

                try:

                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=120000
                    )

                    delay = random.uniform(2, 4) if fast_mode else random.uniform(4, 7)
                    await asyncio.sleep(delay)

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
                        f"[DEBUG] Found {len(ads)} ads on page {page_num}"
                    )
                    
                    if progress_callback:
                        elapsed = time.time() - start_time
                        if elapsed > 5:
                            current_progress = 0.3 + (page_num / max_pages) * 0.1
                            estimated_total = elapsed / current_progress if current_progress > 0 else 0
                            remaining = estimated_total - elapsed
                            progress_callback(
                                current_progress,
                                f"Found {len(ads)} listings on page {page_num} (ETA: {int(remaining)}s)"
                            )
                        else:
                            progress_callback(
                                0.3 + (page_num / max_pages) * 0.1,
                                f"Found {len(ads)} listings on page {page_num}"
                            )

                    if len(ads) == 0:

                        empty_page_count += 1

                        print(
                            f"Empty page detected ({empty_page_count})"
                        )

                        # retry once
                        await asyncio.sleep(
                            random.uniform(10, 20)
                        )

                        continue

                    else:

                        empty_page_count = 0

                    if empty_page_count >= 3:
                        print("Stopping due to repeated empty pages")
                        break

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
                        f"[DEBUG] Extracted {len(links)} unique links"
                    )

                    # Sequential listing parsing

                    for idx, link in enumerate(links):

                        # Stop if we have enough results
                        if len(all_results) >= max_results:
                            print(f"Reached max results ({max_results})")
                            break

                        try:
                            if progress_callback:
                                elapsed = time.time() - start_time
                                current_progress = 0.4 + (len(all_results) / max_results) * 0.5
                                if elapsed > 5:
                                    estimated_total = elapsed / current_progress if current_progress > 0 else 0
                                    remaining = estimated_total - elapsed
                                    progress_callback(
                                        current_progress,
                                        f"Parsing listing {idx + 1}/{len(links)} ({len(all_results)}/{max_results} collected) (ETA: {int(remaining)}s)"
                                    )
                                else:
                                    progress_callback(
                                        current_progress,
                                        f"Parsing listing {idx + 1}/{len(links)} ({len(all_results)}/{max_results} collected)"
                                    )

                            result = await self.parse_listing(
                                page,
                                link,
                                fast_mode=fast_mode
                            )

                            if result:
                                all_results.append(
                                    result
                                )
                                print(f"[DEBUG] Collected {len(all_results)}/{max_results} properties")
                            else:
                                print(f"[DEBUG] Listing returned None (filtered out or error)")

                            delay = random.uniform(2, 4) if fast_mode else random.uniform(4, 8)
                            await asyncio.sleep(delay)

                        except Exception as e:

                            print(
                                f"[DEBUG] Failed listing {link}: {e}"
                            )
                    
                    # Stop if we have enough results
                    if len(all_results) >= max_results:
                        print(f"Reached max results ({max_results}), stopping")
                        break

                    # Delay between pages
                    page_delay = random.uniform(5, 10) if fast_mode else random.uniform(10, 20)
                    await asyncio.sleep(page_delay)

                except Exception as e:

                    print(
                        f"Error on page {page_num}: {e}"
                    )

            await browser.close()

        if progress_callback:
            elapsed = time.time() - start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            progress_callback(1.0, f"✅ Completed! Found {len(all_results)} properties in {time_str}")
        
        print(f"[DEBUG] Total results after all pages: {len(all_results)}")
        return all_results

    async def parse_listing(
            self,
            page,
            url,
            fast_mode=False
    ):

        try:

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=120000
            )

            delay = random.uniform(1, 3) if fast_mode else random.uniform(3, 6)
            await asyncio.sleep(delay)

            await page.mouse.wheel(
                0,
                random.randint(500, 1500) if fast_mode else random.randint(1000, 2500)
            )

            delay = random.uniform(1, 3) if fast_mode else random.uniform(2, 5)
            await asyncio.sleep(delay)

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

            if self.is_investment_property(text, title):
                print(f"[DEBUG] Skipping investment property: {title}")
                return None
            
            # Check for excluded floor types
            if self.is_excluded_floor(text, title):
                print(f"[DEBUG] Skipping excluded floor type: {title}")
                return None
            
            print(f"[DEBUG] Property passed filters: {title}")

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

                "property_type": self.normalize_property_type(details.get("property_type")
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
            "Adlershof",
            "Pankow",
            "Steglitz",
            "Tempelhof",
            "Köpenick",
            "Lichtenberg",
            "Reinickendorf",
            "Neu-Hohenschönhausen",
            "Alt-Hohenschönhausen",
            "Hohenschönhausen",
        ]

        for area in berlin_areas:

            if area.lower() in text.lower():
                return area

        return "Berlin"
