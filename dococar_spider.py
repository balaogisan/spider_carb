#!/usr/bin/env python3
"""
DoCoCAR - 台北 119 家汽車鍍膜店  (含電話)  → dococar_taipei_detailing.xlsx
"""
import re, time, random
from pathlib import Path
import pandas as pd
import cloudscraper                       # ← 自動解 Cloudflare
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE = "https://dococar.com"
LIST_URL = f"{BASE}/coating/taipei"
HEADERS = {"User-Agent":
           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
           "AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36"}
scraper = cloudscraper.create_scraper(browser={"browser": "chrome",
                                               "platform": "darwin",
                                               "mobile": False})

def get_soup(url):
    try:
        response = scraper.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")      # 沒裝 lxml 就改 "html.parser"
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise

# ---------- STEP 1：抓 12 個分頁 ----------
print("STEP 1  取得行政區分頁…")
try:
    district_links = [f"{BASE}/coating/taipei/{i}" for i in range(1, 13)]
    print("  ▶ 生成 12 個分頁連結 ⇒", district_links)
    
except Exception as e:
    logger.error(f"Error in STEP 1: {e}")
    print(f"  ❌ STEP 1 失敗: {e}")
    exit(1)

# ---------- STEP 2：列表擷取店家卡片 ----------
print("STEP 2  擷取店家列表…")
stores = []
for i, link in enumerate(district_links, 1):
    try:
        print(f"  處理分頁 {i}/{len(district_links)}: {link}")
        d_soup = get_soup(link)
        
        # More robust district extraction
        h1_element = d_soup.select_one("h1")
        if h1_element:
            district = h1_element.text.split("台北市")[-1].split("汽")[0]
        else:
            district = f"未知區域{i}"
            logger.warning(f"Could not extract district from {link}")
        
        # Extract store cards
        cards = d_soup.select("a[href^='/detailing/']")
        for card in cards:
            store_name = card.get_text(strip=True)
            if store_name:  # Only add if store name exists
                stores.append({
                    "store_name": store_name,
                    "district":   district,
                    "detail_url": BASE + card["href"]
                })
        
        print(f"    ▶ 找到 {len(cards)} 家店")
        time.sleep(random.uniform(0.5, 1.0))  # Rate limiting
        
    except Exception as e:
        logger.error(f"Error processing district page {link}: {e}")
        continue

print("  ▶ 從列表抓到", len(stores), "間店")

# ---------- STEP 3：逐店擷取電話 / 評分 ----------
phone_re = re.compile(r"\d{2,4}-?\d{3,4}-?\d{3,4}")
def parse_detail(url):
    try:
        s = get_soup(url)
        
        # Extract phone number
        phone_m = phone_re.search(s.get_text())
        phone = phone_m.group(0) if phone_m else ""
        
        # Extract rating - try multiple selectors
        rating_selectors = ['[itemprop="ratingValue"]', '.rating-value', '.star-rating']
        rating = ""
        for selector in rating_selectors:
            rating_elem = s.select_one(selector)
            if rating_elem:
                rating = rating_elem.text.strip()
                break
        
        # Extract reviews count - try multiple selectors  
        review_selectors = ['[itemprop="ratingCount"]', '.review-count', '.reviews-count']
        reviews = ""
        for selector in review_selectors:
            reviews_elem = s.select_one(selector)
            if reviews_elem:
                reviews = reviews_elem.text.strip()
                break
        
        # Extract address - try multiple selectors
        address_selectors = ['[itemprop="address"]', '.address', '.location']
        address = ""
        for selector in address_selectors:
            address_elem = s.select_one(selector)
            if address_elem:
                address = address_elem.text.strip()
                break
        
        return phone, rating, reviews, address
        
    except Exception as e:
        logger.error(f"Error parsing detail page {url}: {e}")
        return "", "", "", ""

print("STEP 3  擷取詳細頁 (約 60 秒)…")
if not stores:
    print("  ⚠️  沒有店家資料，跳過詳細頁擷取")
else:
    for row in tqdm(stores, ncols=80, desc="擷取店家詳細資料"):
        try:
            phone, rating, reviews, addr = parse_detail(row["detail_url"])
            row.update({"phone": phone, "rating": rating,
                        "reviews": reviews, "address": addr})
        except Exception as e:
            logger.error(f"Error processing store {row.get('store_name', 'Unknown')}: {e}")
            row.update({"phone": "", "rating": "", "reviews": "", "address": ""})
        
        # More random sleep to avoid being blocked
        time.sleep(random.uniform(0.8, 1.5))

# ---------- STEP 4：輸出 ----------
if stores:
    df = pd.DataFrame(stores)
    out = Path("dococar_taipei_detailing.xlsx")
    
    # Ensure output directory exists
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to Excel
    try:
        df.to_excel(out, index=False)
        print(f"✅ 完成：{len(df)} 筆  →  {out.resolve()}")
        
        # Show summary statistics
        print("\n📊 資料摘要:")
        print(f"  - 總店家數: {len(df)}")
        print(f"  - 有電話號碼: {len(df[df['phone'] != ''])}")
        print(f"  - 有評分: {len(df[df['rating'] != ''])}")
        print(f"  - 有地址: {len(df[df['address'] != ''])}")
        print(f"  - 行政區分布: {df['district'].value_counts().to_dict()}")
        
    except Exception as e:
        logger.error(f"Error saving to Excel: {e}")
        print(f"❌ 儲存失敗: {e}")
        
        # Try to save as CSV as fallback
        try:
            csv_out = out.with_suffix('.csv')
            df.to_csv(csv_out, index=False)
            print(f"🔄 已改存為 CSV: {csv_out.resolve()}")
        except Exception as csv_e:
            logger.error(f"Error saving CSV: {csv_e}")
            print(f"❌ CSV 儲存也失敗: {csv_e}")
else:
    print("❌ 沒有資料可輸出")
