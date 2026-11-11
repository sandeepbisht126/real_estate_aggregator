import asyncio
import json
import os
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
    def __init__(self, min_price=100000, max_price=600000, min_space=50, max_space=200, min_rooms=1, max_rooms=6):
        self.area = "berlin"
        self.min_price = min_price
        self.max_price = max_price
        self.min_space = min_space
        self.max_space = max_space
        self.min_rooms = min_rooms
        self.max_rooms = max_rooms


# Cache file path
CACHE_FILE = "scraped_properties_cache.json"

def save_to_cache(properties):
    """Save properties to cache file"""
    # Convert datetime objects to strings for JSON serialization
    serializable_props = []
    for prop in properties:
        prop_copy = prop.copy()
        if prop_copy.get("posted_date"):
            prop_copy["posted_date"] = prop_copy["posted_date"].isoformat() if hasattr(prop_copy["posted_date"], 'isoformat') else str(prop_copy["posted_date"])
        serializable_props.append(prop_copy)
    
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "properties": serializable_props
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(properties)} properties to cache")

def load_from_cache(max_age_hours=24):
    """Load properties from cache if recent enough"""
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        age = datetime.now() - cache_time
        
        if age.total_seconds() > max_age_hours * 3600:
            print(f"Cache is {age.total_seconds() / 3600:.1f} hours old, ignoring")
            return None
        
        print(f"Loaded {len(cache_data['properties'])} properties from cache")
        return cache_data["properties"]
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None


def filter_properties(properties, filters):
    """Filter cached properties based on criteria"""
    if not properties:
        return []
    
    filtered = []
    for prop in properties:
        # Price filter
        price = prop.get("price")
        if price and (price < filters.get("min_price", 0) or price > filters.get("max_price", 9999999)):
            continue
        
        # Rooms filter
        rooms = prop.get("rooms")
        if rooms and (rooms < filters.get("min_rooms", 0) or rooms > filters.get("max_rooms", 10)):
            continue
        
        # Space filter
        space = prop.get("living_space")
        if space and (space < filters.get("min_space", 0) or space > filters.get("max_space", 1000)):
            continue
        
        # Area filter (handle multiple areas)
        area = filters.get("area")
        if area and area != "":
            prop_area = str(prop.get("area", "")).lower()
            if "," in area:
                # Multiple areas selected
                area_list = [a.strip().lower() for a in area.split(",")]
                if not any(a in prop_area for a in area_list):
                    continue
            else:
                # Single area
                if area.lower() not in prop_area:
                    continue
        
        filtered.append(prop)
    
    return filtered


async def run(max_scan_pages, use_database=True, max_results=None, fast_mode=False, progress_callback=None, filters=None, use_cache=True):
    klein = KleinanzeigenScraper()
    # immo = ImmoScoutScraper()
    
    # Use provided filters or defaults (broader for scraping)
    if filters:
        filter_obj = Filters(
            min_price=filters.get('min_price', 100000),
            max_price=filters.get('max_price', 600000),
            min_space=filters.get('min_space', 50),
            max_space=filters.get('max_space', 200),
            min_rooms=filters.get('min_rooms', 1),
            max_rooms=filters.get('max_rooms', 6)
        )
    else:
        filter_obj = Filters()

    # Try to load from cache first
    if use_cache and not use_database:
        cached = load_from_cache(max_age_hours=24)
        if cached:
            # Apply selective filters to cached data
            if filters:
                filtered = filter_properties(cached, filters)
                # Sort and limit
                filtered.sort(
                    key=lambda x: x.get("posted_date") or "",
                    reverse=True
                )
                if max_results:
                    filtered = filtered[:max_results]
                print(f"Filtered to {len(filtered)} properties from cache")
                return filtered
            else:
                cached.sort(
                    key=lambda x: x.get("posted_date") or "",
                    reverse=True
                )
                if max_results:
                    cached = cached[:max_results]
                return cached

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
    
    # Save to cache for future use
    if not use_database:
        save_to_cache(all_properties)

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
