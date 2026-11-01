import asyncio
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from models import Property
from scrapers.kleinanzeigen import KleinanzeigenScraper

DATABASE_URL = (
    "postgresql://postgres:postgres@localhost:5432/properties"
)

engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)


class Filters:
    def __init__(self, min_price=200000, max_price=450000, min_space=75, max_space=120, min_rooms=3, max_rooms=4):
        self.area = "berlin"
        self.min_price = min_price
        self.max_price = max_price
        self.min_space = min_space
        self.max_space = max_space
        self.min_rooms = min_rooms
        self.max_rooms = max_rooms


async def run(max_scan_pages, use_database=True, max_results=None, fast_mode=False, progress_callback=None, filters=None):
    klein = KleinanzeigenScraper()
    # immo = ImmoScoutScraper()
    
    # Use provided filters or defaults
    if filters:
        filter_obj = Filters(
            min_price=filters.get('min_price', 200000),
            max_price=filters.get('max_price', 450000),
            min_space=filters.get('min_space', 75),
            max_space=filters.get('max_space', 120),
            min_rooms=filters.get('min_rooms', 3),
            max_rooms=filters.get('max_rooms', 4)
        )
    else:
        filter_obj = Filters()

    results = await asyncio.gather(
        klein.search(filter_obj, max_scan_pages, max_results=max_results, fast_mode=fast_mode, progress_callback=progress_callback),
        # immo.search(Filters())
    )

    all_properties = []

    for r in results:
        all_properties.extend(r)
    
    # Sort by posted date (newest first)
    all_properties.sort(
        key=lambda x: x.get("posted_date") or datetime.min,
        reverse=True
    )
    
    # Apply max_results limit after sorting
    if max_results:
        all_properties = all_properties[:max_results]

    if not use_database:
        print(f"Fast mode: Returning {len(all_properties)} properties without database")
        return all_properties

    session = Session()
    session.execute(text("TRUNCATE TABLE properties RESTART IDENTITY"))

    for item in all_properties:

        exists = (
            session.query(Property)
            .filter_by(url=item["url"])
            .first()
        )

        if exists:
            continue

        property_obj = Property(

            source=item.get("source"),

            title=item.get("title"),

            posted_date=item.get("posted_date"),

            description=item.get("description"),

            city=item.get("city"),

            area=item.get("area"),

            price=item.get("price"),

            living_space=item.get("living_space"),

            rooms=item.get("rooms"),

            bedrooms=item.get("bedrooms"),

            bathrooms=item.get("bathrooms"),

            floor=item.get("floor"),

            property_type=item.get("property_type"),

            year_built=item.get("year_built"),

            balcony=item.get("balcony"),

            hausgeld=item.get("hausgeld"),

            energy_class=item.get("energy_class"),

            available_from=item.get("available_from"),

            provision=item.get("provision"),

            url=item.get("url")
        )

        session.add(property_obj)

    session.commit()

    session.close()

    print(f"Inserted {len(all_properties)} properties")
    return all_properties


if __name__ == "__main__":
    # Fast mode: Get top 10 properties quickly without database
    asyncio.run(run(max_scan_pages=2, use_database=False, max_results=10, fast_mode=True))
    
    # Full mode: Scrape more pages and save to database
    # asyncio.run(run(max_scan_pages=5, use_database=True))
