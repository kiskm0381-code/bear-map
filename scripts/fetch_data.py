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

def fetch_all_hokkaido_news():
    """複数の検索キーワードで全道のヒグマ情報を深掘りして取得する"""
    queries = [
        "北海道 ヒグマ 出没 OR 目撃",
        "札幌 熊 出没",
        "旭川 熊 出没",
        "函館 熊 出没",
        "釧路 熊 出没",
        "帯広 熊 出没",
        "北見 熊 出没",
        "空知 熊 出没",
        "上川 熊 出没",
        "渡島 熊 出没"
    ]
    
    all_new_items = []
    for q_raw in queries:
        query = urllib.parse.quote(q_raw)
        url = NEWS_RSS_URL.format(query=query)
        print(f"Deep fetching: {q_raw}...")
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all('item')
            
            for item in items: # 制限を外して全件取得
                title = item.title.text
                link = item.link.text
                pub_date = item.pubDate.text
                
                # 地名抽出ロジック（改良版）
                place = ""
                if "で" in title:
                    place = title.split("で")[0].split("）")[-1].split("」")[-1]
                elif "）" in title:
                    place = title.split("）")[0].split("（")[-1]
                
                if len(place) > 1 and len(place) < 20:
                    lat, lng = geocode_address(place)
                    if lat:
                        # 地点の重複（全く同じ場所）を避けるためのキー
                        s_id = hashlib.md5(f"{place}{title[:10]}".encode()).hexdigest()[:10]
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
            time.sleep(1) # APIへの負荷軽減
        except Exception as e:
            print(f"Error fetching {q_raw}: {e}")
            
    return all_new_items

def merge_data(new_sightings):
    """既存のデータとマージして保存"""
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            existing = []
    else:
        existing = []

    existing_ids = {s['id'] for s in existing}
    added = 0
    for item in new_sightings:
        if item['id'] not in existing_ids:
            existing.append(item)
            added += 1
    
    # 30日以上前の古いデータを削除（任意）
    # ...

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=4)
    
    print(f"Update complete. Added {added} new sightings across Hokkaido.")

if __name__ == "__main__":
    # 札幌市公式 + 全道ニュース のハイブリッド
    all_data = []
    # 札幌
    # all_data.extend(fetch_sapporo_live()) # 先ほど実装した関数
    # 全道
    all_data.extend(fetch_all_hokkaido_news())
    
    if all_data:
        merge_data(all_data)
    else:
        print("No new data found.")
