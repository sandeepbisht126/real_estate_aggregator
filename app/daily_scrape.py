"""
Daily script to scrape latest properties.
Run this daily (e.g., via Windows Task Scheduler or cron) to get the latest properties.
"""
import asyncio
from datetime import datetime
from main import run


async def daily_run():
    """Run daily scrape to get latest 10 properties quickly."""
    print(f"\n{'='*50}")
    print(f"Daily Scrape - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        # Fast mode: Get top 10 latest properties without database
        properties = await run(
            max_scan_pages=2,
            use_database=False,
            max_results=10,
            fast_mode=True
        )
        
        print(f"\n{'='*50}")
        print(f"Successfully scraped {len(properties)} properties")
        print(f"{'='*50}\n")
        
        # Print summary of scraped properties
        for i, prop in enumerate(properties, 1):
            print(f"{i}. {prop.get('title', 'N/A')}")
            print(f"   Price: €{prop.get('price', 0):,.0f}")
            print(f"   Rooms: {prop.get('rooms', 'N/A')}")
            print(f"   Posted: {prop.get('posted_date', 'N/A')}")
            print(f"   URL: {prop.get('url', 'N/A')}")
            print()
        
        return properties
        
    except Exception as e:
        print(f"Error during daily scrape: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(daily_run())
