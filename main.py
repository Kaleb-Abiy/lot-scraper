import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import json

# ===================== CONFIG =====================

BASE_URL = "https://bhauction.com"
LIST_URL = "https://bhauction.com/en/result/tas-supergt-auction/lots/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

# ===================== HELPERS =====================

def structured_html(text):
    if not text:
        return None
    return f"<p>{text}</p>"

def get_text(el):
    return el.get_text(" ", strip=True) if el else None

# ===================== LIST PAGE =====================

def get_lot_links():
    r = session.get(LIST_URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = set()
    for a in soup.select(".mod--lots__list__body__item a[href]"):
        links.add(urljoin(BASE_URL, a["href"]))

    return list(links)

# ===================== DETAIL PAGE =====================

def parse_lot_detail(url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # ---------- Lot ----------
    lot_title_el = soup.select_one("h1.title")
    lot_title = structured_html(get_text(lot_title_el)) if lot_title_el else None

    # ---------- Lot number ----------
    lot_number = None
    lot_num_el = soup.select_one(".lots__detail__data__lot_num h2.title")
    if lot_num_el:
        # Get all text, remove whitespace
        text = lot_num_el.get_text(strip=True)
        # Remove "LOT NUMBER" and keep only digits
        lot_number_match = re.search(r'\d+', text)
        if lot_number_match:
            lot_number = lot_number_match.group(0)
    

    # ---------- Lot price type ----------
    lot_price_type = None


    # ---------- Description ----------
    desc_ps = soup.select(".chapter p")
    desc_text = " ".join(p.get_text(" ", strip=True) for p in desc_ps).strip()
    lot_description = structured_html(desc_text) if desc_text else None

    # ---------- Vehicle details ----------
    vehicle_mileage_value = None
    vehicle_mileage_unit = None
    vehicle_body_color = None
    vehicle_chassis_no = None
    vehicle_year = None
    vehicle_make = None
    vehicle_model = None
    vehicle_transmission_type = None
    vehicle_steering_position = None
    vehicle_convertible = None
    vehicle_registry_code = None
    vehicle_interior_color = None

    #-------------- Vehicle Mieleage and Chassis -------------
    table = soup.select_one(".lots__detail__data__specific__table")
    if table:
        for row in table.select("tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True).lower()
            value = td.get_text(strip=True)
            
            if "chassis" in key:
                vehicle_chassis_no = value
            elif "mileage" in key or "走行距離" in key:  # add Japanese just in case
                # Split value into number + unit
                m = re.match(r'([\d,]+)\s*(km|mi)', value, re.I)
                if m:
                    vehicle_mileage_value = int(m.group(1).replace(",", ""))
                    vehicle_mileage_unit = m.group(2).lower()
    

    # -----------vehicle Price and currency detail----------
    price_el = soup.select_one(".lots__detail__data__estimate .price")
    lot_estimate_low = None
    lot_estimate_high = None
    lot_currency = None
    if price_el:
        # Combine all text nodes (handles <br> tags)
        price_text = " ".join(price_el.stripped_strings).strip()  # e.g. "¥9,000,000 - ¥13,000,000" or "SOLD AFTER AUCTION"

        # Check for non-numeric sold text
        if re.search(r"\bsold\b", price_text, re.I):
            lot_price_type = "sold"
            lot_currency = None
            lot_estimate_low = None
            lot_estimate_high = None
        else:
            # Split by dash
            if "-" in price_text:
                low_str, high_str = price_text.split("-", 1)
                currency_match = re.match(r"([^\d]+)", low_str.strip())
                if currency_match:
                    lot_currency = currency_match.group(1).strip()
                # Convert to int safely
                low_digits = re.sub(r"[^\d]", "", low_str)
                high_digits = re.sub(r"[^\d]", "", high_str)
                lot_estimate_low = int(low_digits) if low_digits else None
                lot_estimate_high = int(high_digits) if high_digits else None
                lot_price_type = "highest_bid"
            else:
                currency_match = re.match(r"([^\d]+)", price_text.strip())
                if currency_match:
                    lot_currency = currency_match.group(1).strip()
                digits = re.sub(r"[^\d]", "", price_text)
                lot_estimate_low = int(digits) if digits else None
                lot_estimate_high = lot_estimate_low
                lot_price_type = "highest_bid" if digits else None

    # ----------- Other fields that might we get with regex---------
    if desc_text:
        # Body color
        m = re.search(r'painted in\s+([a-zA-Z\s\(\)]+)', desc_text, re.I)
        if m:
            vehicle_body_color = m.group(1).strip()

        # Steering
        if re.search(r'\bleft[- ]hand drive\b', desc_text, re.I):
            vehicle_steering_position = "left"
        elif re.search(r'\bright[- ]hand drive\b', desc_text, re.I):
            vehicle_steering_position = "right"

        # Convertible
        if re.search(r'\bconvertible\b', desc_text, re.I):
            vehicle_convertible = True

    # ---------- Images ----------
    images = []
    for img in soup.select("img[data-src]"):
        src = img.get("data-src")
        if src and not any(x in src.lower() for x in ["logo", "icon", "ui"]):
            images.append(src)
    images = list(dict.fromkeys(images)) or None

    return {
        "lot_source_link": url,
        "lot_number": lot_number,
        "lot_sold_date": None,
        "lot_title": lot_title,
        "lot_description": lot_description,
        "lot_estimate_low": lot_estimate_low,
        "lot_estimate_high": lot_estimate_high,
        "lot_currency": lot_currency,
        "lot_price_type": lot_price_type,
        "lot_price_value": None,
        "lot_is_no_reserve": None,
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "vehicle_year": vehicle_year,
        "vehicle_chassis_no": vehicle_chassis_no,
        "vehicle_transmission_type": vehicle_transmission_type,
        "vehicle_steering_position": vehicle_steering_position,
        "vehicle_body_color": vehicle_body_color,
        "vehicle_interior_color": vehicle_interior_color,
        "vehicle_convertible": vehicle_convertible,
        "vehicle_registry_code": vehicle_registry_code,
        "vehicle_mileage_value": vehicle_mileage_value,
        "vehicle_mileage_unit": vehicle_mileage_unit,
        "images": images
    }


def get_auction_info():
    """Scrape auction-level data from the list page."""
    resp = requests.get(LIST_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    title_tag = soup.select_one("div.auction__list__item__information h1.title")
    date_tag = soup.select_one("div.auction__list__item__information p.date")
    location_tag = soup.select_one("div.auction__list__item__information p.location")
    
    auction_title = title_tag.get_text(strip=True) if title_tag else None
    auction_date = date_tag.get_text(strip=True) if date_tag else None
    auction_location = location_tag.get_text(strip=True) if location_tag else None

    # Auctioneer is in the footer's site name
    auctioneer_tag = soup.select_one("meta[property='og:site_name']")
    auctioneer = auctioneer_tag["content"] if auctioneer_tag else None
    
    return auction_title, auction_date, auction_location, auctioneer

# ===================== MAIN =====================
def scrape():
    items = []

    # Get auction-level info once
    auction_title, auction_date, auction_location, auctioneer = get_auction_info()

    for link in get_lot_links():
        item = parse_lot_detail(link)
        items.append(item)

    return {
        "schema_version": "auction_v1",
        "job_run_date": datetime.utcnow().isoformat(),
        "auction_title": auction_title,
        "auction_date": auction_date,
        "auction_location": auction_location,
        "auctioneer": auctioneer,
        "items": items
    }

# ===================== RUN =====================

if __name__ == "__main__":
    data = scrape()
    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    print(json_data)

