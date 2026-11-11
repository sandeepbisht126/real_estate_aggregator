
# Fast Mode - Quick Property Scraping

## Overview
The scraper now supports a fast mode that quickly fetches the latest 10 properties without database operations, optimized for daily runs.

## Key Improvements

### 1. **Fast Mode Parameters**
- **max_results**: Stops scraping after collecting N properties (default: 10)
- **fast_mode**: Reduces delays between requests (2-4s instead of 4-8s)
- **use_database**: Skips database operations for faster execution
- **max_scan_pages**: Limits pages to scrape (2 pages in fast mode vs 5 in full mode)

### 2. **Early Filtering**
Properties are filtered during scraping to save time:
- **Price**: 200k - 450k EUR
- **Rooms**: 3 - 4 rooms
- **Floor Types**: Excludes ground floor (erdgeschoss), attic (dachgeschoss), basement (souterrain/keller)
- **Investment Properties**: Excludes kapitalanlage, vermietete wohnung, etc.

### 3. **Performance Comparison**
- **Full Mode**: ~30-60 minutes (5 pages, full delays, database)
- **Fast Mode**: ~5-10 minutes (2 pages, reduced delays, no database)

## Usage

### Manual Fast Scrape
```bash
cd D:\Python\real_estate_aggregator\app
python daily_scrape.py
```

### Streamlit Dashboard
1. Run the dashboard: `streamlit run app/streamlit_ui/dashboard.py`
2. Check "🔄 Fast Scrape (Latest 10 Properties)" in the sidebar
3. Click "🚀 Apply Filters" to scrape latest properties

### Daily Automation (Windows Task Scheduler)

1. **Create a batch script** (`run_daily_scrape.bat`):
```batch
@echo off
cd /d D:\Python\real_estate_aggregator\app
python daily_scrape.py
```

2. **Open Task Scheduler**:
   - Press Win+R, type `taskschd.msc`

3. **Create Basic Task**:
   - Name: "Daily Property Scrape"
   - Trigger: Daily (e.g., 9:00 AM)
   - Action: Start a program
   - Program: `C:\path\to\run_daily_scrape.bat`

4. **Test the task** manually before enabling.

### Daily Automation (Linux/Mac Cron)
```bash
# Edit crontab
crontab -e

# Add daily job at 9:00 AM
0 9 * * * cd /path/to/real_estate_aggregator/app && python daily_scrape.py >> scrape.log 2>&1
```

## Configuration

### Adjust Filters in `app/main.py`:
```python
class Filters:
    area = "berlin"
    min_price = 200000      # Adjust as needed
    max_price = 450000      # Adjust as needed
    min_space = 75
    max_space = 120
    min_rooms = 3           # Adjust as needed
    max_rooms = 4           # Adjust as needed
```

### Adjust Excluded Floor Types in `app/scrapers/kleinanzeigen.py`:
```python
EXCLUDED_FLOOR_TYPES = [
    "erdgeschoss",  # Ground floor
    "dachgeschoss", # Attic
    "souterrain",   # Basement
    "keller"        # Cellar
]
```

## Running Full Mode (Database)
To run the full scraper with database storage:
```bash
cd D:\Python\real_estate_aggregator\app
python main.py
```

Or modify `main.py` to uncomment:
```python
if __name__ == "__main__":
    # Full mode: Scrape more pages and save to database
    asyncio.run(run(max_scan_pages=5, use_database=True))
```

## Notes
- Fast mode still respects rate limiting to avoid blocking
- Properties are sorted by posted date (newest first)
- Investment properties and excluded floor types are filtered early to save time
- Streamlit dashboard supports both fast scrape and database modes
