# Spider for shop Info

A web scraper for extracting automotive detailing shop information from DoCoCAR website, specifically targeting Taipei area shops.

## Overview

This Python script scrapes automotive detailing shop data from DoCoCAR (https://dococar.com), extracting information about car coating/detailing shops in Taipei. The scraper navigates through 12 district pages and collects detailed information for each shop.

## Features

- **Anti-bot protection**: Uses CloudScraper to bypass Cloudflare protection
- **Comprehensive data extraction**: Collects shop names, locations, phone numbers, ratings, and addresses
- **Rate limiting**: Implements random delays to avoid being blocked
- **Progress tracking**: Uses tqdm for progress visualization
- **Error handling**: Robust error handling with logging
- **Multiple output formats**: Primary Excel output with CSV fallback

## Dependencies

- `pandas` - Data manipulation and Excel output
- `cloudscraper` - Cloudflare bypass
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `tqdm` - Progress bars
- `requests` - HTTP requests (via cloudscraper)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd spider_carb
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install pandas cloudscraper beautifulsoup4 lxml tqdm requests
```

## Usage

Run the spider:
```bash
python dococar_spider.py
```

The script will:
1. Generate 12 district page URLs for Taipei
2. Extract shop information from each district page
3. Visit each shop's detail page to collect additional information
4. Save the results to `dococar_taipei_detailing.xlsx`

## Output

The script generates an Excel file (`dococar_taipei_detailing.xlsx`) with the following columns:
- `store_name`: Name of the detailing shop
- `district`: Taipei district location
- `detail_url`: URL to the shop's detail page
- `phone`: Phone number
- `rating`: Customer rating
- `reviews`: Number of reviews
- `address`: Full address

## Data Summary

After completion, the script displays:
- Total number of shops found
- Number of shops with phone numbers
- Number of shops with ratings
- Number of shops with addresses
- Distribution by district

## Error Handling

- Comprehensive logging with timestamps
- Graceful handling of network errors
- Fallback to CSV if Excel save fails
- Continues processing even if individual shops fail

## Rate Limiting

The script implements respectful crawling with:
- Random delays between requests (0.5-1.0 seconds for listing pages)
- Longer delays for detail pages (0.8-1.5 seconds)
- Timeout settings for all requests

## Legal Notice

This scraper is for educational purposes. Please ensure you comply with the website's terms of service and robots.txt file before running the scraper on their servers.