"""
Script to scrape with broad filters and save to cache.
Run this to populate the cache with a broad set of properties.
"""
import asyncio
from main import run, Filters


async def scrape_broad_to_cache():
    """Scrape with broad filters and save to cache."""
    print(f"\n{'='*60}")
    print("Scraping with BROAD filters to populate cache...")
    print(f"{'='*60}\n")
    
    # Use broad filters for scraping
    broad_filters = {
        'min_price': 100000,
        'max_price': 600000,
        'min_space': 50,
        'max_space': 200,
        'min_rooms': 1,
        'max_rooms': 6,
        'area': ''  # Empty = all areas
    }
    
    try:
        # Scrape more pages to get broader results
        properties = await run(
            max_scan_pages=3,  # Scrape 3 pages for broader results
            use_database=False,
            max_results=50,  # Get up to 50 properties
            fast_mode=True,
            progress_callback=None,
            filters=broad_filters,
            use_cache=False  # Force fresh scrape
        )
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully scraped and cached {len(properties)} properties")
        print(f"{'='*60}\n")
        
        # Print summary
        print("Summary of scraped properties:")
        for i, prop in enumerate(properties[:10], 1):
            print(f"{i}. {prop.get('title', 'N/A')[:60]}")
            print(f"   Price: €{prop.get('price', 0):,.0f} | Rooms: {prop.get('rooms', 'N/A')} | Area: {prop.get('area', 'N/A')}")
        
        if len(properties) > 10:
            print(f"\n... and {len(properties) - 10} more properties")
        
        return properties
        
    except Exception as e:
        print(f"Error during scrape: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(scrape_broad_to_cache())
