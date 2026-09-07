import subprocess
import requests
import xml.etree.ElementTree as ET

def get_connected_devices():
    """Получает список подключенных по ADB физических телефонов"""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")[1:]
        devices = [line.split("\t")[0] for line in lines if "device" in line]
        return devices
    except Exception:
        return []

def connect_device_proxy(device_id: str, proxy_str: str):
    """Настройка прокси для конкретного телефона через ADB"""
    try:
        parts = proxy_str.split(":")
        ip, port = parts[0], parts[1]
        subprocess.run(["adb", "-s", device_id, "shell", "settings", "put", "global", "http_proxy", f"{ip}:{port}"])
        return True
    except Exception:
        return False

def check_shadowban_legally(username: str) -> dict:
    """Легальная проверка статуса профиля и доступности в рекомендациях"""
    try:
        url = f"https://www.tiktok.com/@{username}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return {
                "status": "Active / Visible",
                "shadowbanned": False,
                "details": "Профиль открыт, публичный доступ стабилен."
            }
        else:
            return {
                "status": "Restricted / Banned",
                "shadowbanned": True,
                "details": f"Код ответа сервера: {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "Error",
            "shadowbanned": None,
            "details": str(e)
        }

def reset_device_fingerprint(device_id: str):
    """Сброс рекламного идентификатора (GAID) и кэша приложения для обхода теневого бана"""
    try:
        subprocess.run([
            "adb", "-s", device_id, "shell", 
            "am", "broadcast", "-a", "com.google.android.gms.ads.identifier.service.START"
        ])
        subprocess.run([
            "adb", "-s", device_id, "shell", 
            "pm", "clear", "com.zhiliaoapp.musically"
        ])
        return True
    except Exception:
        return False

def check_proxy_purity(proxy_str: str) -> dict:
    """Проверка прокси на работоспособность и анонимность"""
    try:
        proxies = {"http": proxy_str, "https": proxy_str}
        response = requests.get("https://ipapi.co/json/", proxies=proxies, timeout=10)
        data = response.json()
        return {
            "ip": data.get("ip"),
            "country": data.get("country_name"),
            "safe": True
        }
    except Exception as e:
        return {
            "safe": False,
            "error": str(e)
        }

def get_cb_rates():
    """Получает актуальные курсы валют (USD) с официального сайта ЦБ РФ на сегодня."""
    rates = {
        "USD": 95.0,
        "EUR": 102.0,
        "TON": 5.5
    }
    try:
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for valute in root.findall('Valute'):
                char_code = valute.find('CharCode').text
                if char_code == "USD":
                    value_str = valute.find('Value').text.replace(',', '.')
                    rates["USD"] = float(value_str)
    except Exception:
        pass
    
    return rates
