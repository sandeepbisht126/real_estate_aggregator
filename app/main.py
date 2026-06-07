import asyncio

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
    area = "berlin"
    min_price = 200000
    max_price = 350000
    min_space = 75
    max_space = 120
    min_rooms = 3
    max_rooms = 5


async def run(max_scan_pages):
    klein = KleinanzeigenScraper()
    # immo = ImmoScoutScraper()

    results = await asyncio.gather(
        klein.search(Filters(), max_scan_pages),
        # immo.search(Filters())
    )

    all_properties = []

    for r in results:
        all_properties.extend(r)

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

            property_type=normalize_property_type(item.get("property_type")),

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


def normalize_property_type(value):
    value = value.lower()

    if "haus" in value:
        return "House"

    return "Apartment"


if __name__ == "__main__":
    asyncio.run(run(max_scan_pages=5))
