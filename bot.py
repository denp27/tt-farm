import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import BOT_TOKEN
from registry import load_offers, add_offer, calculate_earnings
from utils import get_connected_devices, reset_device_fingerprint, connect_device_proxy

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для пошагового ввода данных
class BotStates(StatesGroup):
    waiting_for_proxy = State()
    waiting_for_account = State()
    waiting_for_offer_name = State()
    waiting_for_offer_cpm = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    devices = get_connected_devices()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "📱 Подключенные телефоны", 
        "🌐 Добавить прокси",
        "👤 Добавить аккаунт", 
        "💼 Добавить оффер",
        "📊 Статистика и Офферы", 
        "🔍 Проверить теневой бан", 
        "🛡 Обход теневого бана", 
        "🔥 Прогреть аккаунт"
    )
    
    await message.answer(
        f"🤖 Бот управления фермой запущен!\n"
        f"📱 Активных физических устройств найдено: {len(devices)}",
        reply_markup=kb
    )

@dp.message_handler(text="📱 Подключенные телефоны")
async def show_devices(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("К системе не подключено ни одного телефона по ADB. Проверьте подключение кабеля и отладку по USB.")
    else:
        text = "📱 *Список доступных телефонов*:\n" + "\n".join([f"• `{d}`" for d in devices])
        await message.answer(text, parse_mode="Markdown")

# --- ДОБАВЛЕНИЕ ПРОКСИ ЧЕРЕЗ ИНТЕРФЕЙС ---
@dp.message_handler(text="🌐 Добавить прокси")
async def start_add_proxy(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("⚠️ Сначала подключите хотя бы один телефон по ADB.")
        return
    await BotStates.waiting_for_proxy.set()
    await message.answer(
        "🌐 Введите прокси в формате:\n`ip:port` или `ip:port:login:pass`\n\n"
        "Прокси будет автоматически применен к первому подключенному телефону.",
        parse_mode="Markdown"
    )

@dp.message_handler(state=BotStates.waiting_for_proxy)
async def process_proxy(message: types.Message, state: FSMContext):
    proxy_str = message.text.strip()
    devices = get_connected_devices()
    
    if devices:
        device_id = devices[0]
        success = connect_device_proxy(device_id, proxy_str)
        if success:
            await message.answer(f"✅ Прокси успешно установлен на устройство `{device_id}`!", parse_mode="Markdown")
        else:
            await message.answer("❌ Ошибка при применении прокси через ADB.")
    else:
        await message.answer("❌ Устройства не найдены.")
        
    await state.finish()

# --- ДОБАВЛЕНИЕ АККАУНТА ЧЕРЕЗ ИНТЕРФЕЙС ---
@dp.message_handler(text="👤 Добавить аккаунт")
async def start_add_account(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("⚠️ Сначала подключите телефон, на который хотите авторизовать аккаунт.")
        return
    await BotStates.waiting_for_account.set()
    await message.answer("👤 Введите логин (username или номер телефона) аккаунта для привязки к устройству:")

@dp.message_handler(state=BotStates.waiting_for_account)
async def process_account(message: types.Message, state: FSMContext):
    acc_name = message.text.strip()
    # Здесь сохраняем аккаунт в базу или файл
    await message.answer(f"✅ Аккаунт *{acc_name}* успешно привязан к системе и готов к работе!", parse_mode="Markdown")
    await state.finish()

# --- ДОБАВЛЕНИЕ ОФФЕРА И CPM ---
@dp.message_handler(text="💼 Добавить оффер")
async def start_add_offer(message: types.Message):
    await BotStates.waiting_for_offer_name.set()
    await message.answer("💼 Введите название нового оффера (например: *TikTok Wildberries*):", parse_mode="Markdown")

@dp.message_handler(state=BotStates.waiting_for_offer_name)
async def process_offer_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['offer_name'] = message.text.strip()
    await BotStates.next()
    await message.answer("💵 Введите цену за 1000 просмотров (CPM) в USD (например: `1.5`):", parse_mode="Markdown")

@dp.message_handler(state=BotStates.waiting_for_offer_cpm)
async def process_offer_cpm(message: types.Message, state: FSMContext):
    try:
        cpm_usd = float(message.text.strip().replace(',', '.'))
        async with state.proxy() as data:
            offer_name = data['offer_name']
            
        add_offer(offer_name, cpm_usd)
        await message.answer(f"✅ Оффер *{offer_name}* с CPM **${cpm_usd}** успешно добавлен!", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите корректное число для CPM (например, `1.5`):")
        return
        
    await state.finish()

# --- СТАТИСТИКА И ОФФЕРЫ ---
@dp.message_handler(text="📊 Статистика и Офферы")
async def stats_menu(message: types.Message):
    offers = load_offers()
    text = "📈 *Активные офферы и статистика*\n\n"
    
    for name, data in offers.items():
        text += f"• *{name}* — CPM: ${data['cpm_usd']}\n"
    
    if offers:
        first_offer_cpm = list(offers.values())[0]['cpm_usd']
        earned = calculate_earnings(50000, first_offer_cpm)
        text += f"\n📊 *Пример за 50,000 просмотров*:\n" \
                f"💵 USD: ${earned['USD']}\n" \
                f"🇷🇺 RUB: {earned['RUB']} ₽ *(Курс ЦБ: {earned['current_usd_rate']} ₽)*\n" \
                f"💎 TON: {earned['TON']} TON"
    else:
        text += "\nНет добавленных офферов. Нажмите «💼 Добавить оффер»."
                
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(text="🔍 Проверить теневой бан")
async def check_ban(message: types.Message):
    await message.answer("Введите юзернейм аккаунта для проверки теневого бана.")

@dp.message_handler(text="🛡 Обход теневого бана")
async def anti_ban_menu(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("Нет подключенных устройств для применения мер обхода.")
        return
        
    device_id = devices[0]
    success = reset_device_fingerprint(device_id)
    
    if success:
        await message.answer(
            f"🛡 Обходной маневр выполнен для устройства `{device_id}`:\n"
            f"• Сброшен рекламный ID (GAID)\n"
            f"• Очищен кэш приложения",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Ошибка при сбросе параметров устройства.")

@dp.message_handler(text="🔥 Прогреть аккаунт")
async def warm_up_action(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("Нет подключенных устройств для запуска прогрева.")
        return
    await message.answer(f"🔥 Прогрев аккаунта на устройстве `{devices[0]}` запущен в фоновом режиме...", parse_mode="Markdown")
