#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取 DoCoCAR 台北 119 家汽車鍍膜店家詳細資料（含電話）並輸出 Excel
需求：pip install requests beautifulsoup4 pandas openpyxl tqdm
"""

import re, time, random, json, csv
from pathlib import Path
import requests, pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE = "https://dococar.com"
LIST_URL = f"{BASE}/coating/taipei"
HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# ---------- STEP 1：抓 12 行政區分頁 ----------
print("STEP 1: 抓列表頁…")
resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

district_links = [
    BASE + a["href"] for a in soup.select("a[href^='/coating/taipei/']")
]
district_links = list(dict.fromkeys(district_links))  # 去重
print("共偵測到行政區分頁", len(district_links), "頁")

# ---------- STEP 2：在每頁抓店家卡片 ----------
stores = []
for d_link in district_links:
    d_html = requests.get(d_link, headers=HEADERS, timeout=20).text
    d_soup = BeautifulSoup(d_html, "lxml")
    district = d_soup.select_one("h1").text.split("台北市")[-1].split("汽")[0]
    for card in d_soup.select("a[href^='/detailing/']"):
        href = card["href"]
        store_name = card.select_one(".title").text.strip()
        stores.append({
            "store_name": store_name,
            "district": district,
            "detail_url": BASE + href
        })
print("列表頁共取得", len(stores), "間店")

# ---------- STEP 3：逐一訪問 detailing 抓電話等 ----------
def parse_detail(url: str):
    html = requests.get(url, headers=HEADERS, timeout=20).text
    s = BeautifulSoup(html, "lxml")
    # 電話
    phone_match = re.search(r"(\d{2,4}-?\d{3,4}-?\d{3,4})", s.text)
    phone = phone_match.group(1) if phone_match else ""
    # 评分與評論數
    rating = s.select_one('[itemprop="ratingValue"]')
    rating = rating.text.strip() if rating else ""
    reviews = s.select_one('[itemprop="ratingCount"]')
    reviews = reviews.text.strip() if reviews else ""
    # 地址
    address = s.select_one('[itemprop="address"]')
    address = address.text.strip() if address else ""
    return phone, rating, reviews, address

print("STEP 3: 抓取各店詳細頁（請稍候）…")
for row in tqdm(stores, ncols=80):
    try:
        phone, rating, reviews, address = parse_detail(row["detail_url"])
        row.update({"phone": phone, "rating": rating,
                    "reviews": reviews, "address": address})
    except Exception as e:
        row.update({"phone": "", "rating": "", "reviews": "", "address": ""})
    time.sleep(random.uniform(0.5, 1.2))  # 和緩請求

# ---------- STEP 4：輸出 ----------
df = pd.DataFrame(stores)
out_path = Path("dococar_taipei_detailing.xlsx")
df.to_excel(out_path, index=False)
print("✅ 完成！共有", len(df), "筆；已輸出", out_path.resolve())

