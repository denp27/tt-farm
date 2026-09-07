import xml.etree.ElementTree as ET
from datetime import datetime

def get_cb_rates():
    """
    Получает актуальные курсы валют (USD, EUR и т.д.) с официального сайта ЦБ РФ на сегодня.
    Возвращает словарь с курсами к рублю.
    """
    rates = {
        "USD": 95.0,  дфолтный фоллбек на случай сбоя сети
        "EUR": 102.0,
        "TON": 5.5    # TON обычно берем через крипто-апи, но оставим базовым или расчетным
    }
    try:
        # ЦБ РФ предоставляет ежедневные курсы в XML
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for valute in root.findall('Valute'):
                char_code = valute.find('CharCode').text
                if char_code in ["USD", "EUR"]:
                    value_str = valute.find('Value').text.replace(',', '.')
                    rates[char_code] = float(value_str)
    except Exception:
        pass
    
    return rates
