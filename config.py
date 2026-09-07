import os

# Базовые настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Настройки прокси и мобильных подключений
ADB_DEFAULT_PORT = 5037
USE_PHYSICAL_DEVICES = True
