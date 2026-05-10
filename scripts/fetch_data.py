import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
import hashlib
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import urllib.parse
import re

# --- Configuration ---
SAPPORO_URL = "https://www.city.sapporo.jp/kurashi/animal/choju/kuma/syutsubotsu/index.html"
# 全道のニュースを取得するためのRSS
NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sightings.json")

# ジオコーダーの初期化
geolocator = Nominatim(user_agent="bear_alert_hokkaido_v1")

def geocode_address(address):
    """住所文字列を緯度経度に変換する"""
    if not address: return None, None
    # 市町村名が含まれていない場合に備え、「北海道」を付与
    full_address = f"北海道{address}"
    try:
        location = geolocator.geocode(full_address)
        if location:
            return location.latitude, location.longitude
        # 市町村名だけで再試行
        municipality = address.split(" ")[0].split("　")[0]
        location = geolocator.geocode(f"北海道{municipality}")
        if location:
            return location.latitude, location.longitude
    except Exception:
        return None, None
    return None, None

def fetch_sapporo_official():
    """札幌市の全テーブルから正確な座標付きで取得する"""
    print("Fetching Sapporo official tables...")
    try:
        response = requests.get(SAPPORO_URL, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 5: # No, 日時, 場所, 地図, 内容
                    date = tds[1].get_text(separator=" ").strip()
                    place = tds[2].text.strip()
                    map_link = tds[3].find('a')
                    desc = tds[4].text.strip()
                    
                    lat, lng = None, None
                    if map_link and 'href' in map_link.attrs:
                        href = map_link['href']
                        # URLから ll=43.123,141.123 を抽出
                        coord_match = re.search(r'll=([0-9.]+)(?:%2C|,)([0-9.]+)', href)
                        if coord_match:
                            lat = float(coord_match.group(1))
                            lng = float(coord_match.group(2))
                    
                    if lat:
                        s_id = hashlib.md5(f"{place}{date}".encode()).hexdigest()[:10]
                        items.append({
                            "id": s_id,
                            "lat": lat,
                            "lng": lng,
                            "datetime": date,
                            "address": f"札幌市{place}",
                            "description": desc,
                            "source_name": "札幌市公式",
                            "source_url": SAPPORO_URL,
                            "type": "公式確認"
                        })
        return items
    except Exception as e:
        print(f"Sapporo Error: {e}")
        return []

def fetch_all_hokkaido_news():
    """全道のニュースから出典付きで取得する"""
    # より広範囲に、確実なニュースを取得
    queries = ["北海道 熊 出没", "旭川 熊 目撃", "函館 熊 出没", "帯広 熊 出没", "釧路 熊"]
    all_new_items = []
    processed_links = set()
    
    for q_raw in queries:
        query = urllib.parse.quote(q_raw)
        url = NEWS_RSS_URL.format(query=query)
        print(f"Searching news: {q_raw}...")
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all('item')
            
            for item in items[:6]:
                title = item.title.text
                link = item.link.text
                if link in processed_links: continue
                processed_links.add(link)
                
                # 札幌市の情報は公式で取っているのでスキップ
                if "札幌" in title: continue

                # 地名抽出（簡易）
                place = ""
                if "で" in title:
                    place = title.split("で")[0].split("）")[-1].split("」")[-1]
                
                if place and len(place) > 1:
                    lat, lng = geocode_address(place)
                    if lat:
                        s_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()[:10]
                        all_new_items.append({
                            "id": s_id,
                            "lat": lat,
                            "lng": lng,
                            "datetime": datetime.now().isoformat(),
                            "address": place,
                            "description": title,
                            "source_name": "ニュース報道",
                            "source_url": link,
                            "type": "目撃/出没"
                        })
            time.sleep(1)
        except: continue
    return all_new_items

def merge_data(new_sightings):
    """最新データで更新"""
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_sightings, f, ensure_ascii=False, indent=4)
    print(f"Update complete. Total {len(new_sightings)} precise sightings stored.")

if __name__ == "__main__":
    results = []
    results.extend(fetch_sapporo_official())
    results.extend(fetch_all_hokkaido_news())
    
    if results:
        merge_data(results)
    else:
        print("No valid data found.")
