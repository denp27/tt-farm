import json
import os
from utils import get_cb_rates

OFFERS_FILE = "offers.json"

def load_offers():
    if not os.path.exists(OFFERS_FILE):
        return {}
    with open(OFFERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_offers(offers):
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=4)

def add_offer(offer_name: str, cpm_usd: float):
    offers = load_offers()
    offers[offer_name] = {
        "cpm_usd": cpm_usd
    }
    save_offers(offers)

def calculate_earnings(views: int, cpm_usd: float):
    """Рассчитывает доход в USD, RUB (по курсу ЦБ) и TON"""
    rates = get_cb_rates()
    usd_rate = rates.get("USD", 95.0)
    ton_rate = 5.5
    
    total_usd = (views / 1000.0) * cpm_usd
    total_rub = total_usd * usd_rate
    total_ton = total_usd / ton_rate
    
    return {
        "USD": round(total_usd, 2),
        "RUB": round(total_rub, 2),
        "TON": round(total_ton, 4),
        "current_usd_rate": usd_rate
    }
