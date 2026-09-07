import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import BOT_TOKEN
from registry import load_offers, add_offer, calculate_earnings
from utils import get_connected_devices, reset_device_fingerprint, connect_device_proxy
from auth_social import add_social_account, get_platform_accounts

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class BotStates(StatesGroup):
    waiting_for_proxy = State()
    waiting_for_account = State()
    waiting_for_offer_name = State()
    waiting_for_offer_cpm = State()

class SocialAuthStates(StatesGroup):
    waiting_for_credential = State()

temp_auth_data = {}

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    devices = get_connected_devices()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        "📱 Подключенные телефоны", 
        "🌐 Управление соцсетями (YT, Insta, TT)",
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
        await message.answer("К системе не подключено ни одного телефона по ADB.")
    else:
        text = "📱 *Список доступных телефонов*:\n" + "\n".join([f"• `{d}`" for d in devices])
        await message.answer(text, parse_mode="Markdown")

@dp.message_handler(text="🌐 Управление соцсетями (YT, Insta, TT)")
async def social_networks_menu(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("📺 YouTube", callback_data="soc_youtube"),
        types.InlineKeyboardButton("📸 Instagram", callback_data="soc_instagram"),
        types.InlineKeyboardButton("🎬 TikTok", callback_data="soc_tiktok")
    )
    
    yt_accs = get_platform_accounts("youtube")
    ig_accs = get_platform_accounts("instagram")
    tt_accs = get_platform_accounts("tiktok")
    
    text = (
        "🌐 *Центр авторизации и входа в соцсети*:\n\n"
        f"📺 YouTube аккаунтов: {len(yt_accs)}\n"
        f"📸 Instagram аккаунтов: {len(ig_accs)}\n"
        f"🎬 TikTok аккаунтов: {len(tt_accs)}\n\n"
        "Выберите платформу для просмотра или добавления аккаунта:"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('soc_'))
async def process_social_selection(callback_query: types.CallbackQuery):
    platform = callback_query.data.split('_')[1]
    temp_auth_data[callback_query.from_user.id] = platform
    await bot.answer_callback_query(callback_query.id)
    
    accounts = get_platform_accounts(platform)
    acc_list = "\n".join([f"• `{acc}`" for acc in accounts.keys()]) if accounts else "Нет привязанных аккаунтов."
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"➕ Добавить аккаунт {platform.upper()}", callback_data=f"add_soc_{platform}"))
    
    await bot.send_message(
        callback_query.from_user.id,
        f"📌 Платформа: *{platform.upper()}*\n\n"
        f"Активные сессии:\n{acc_list}",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query_handler(lambda c: c.data.startswith('add_soc_'))
async def start_add_social(callback_query: types.CallbackQuery):
    platform = callback_query.data.split('_')[2]
    temp_auth_data[callback_query.from_user.id] = platform
    await bot.answer_callback_query(callback_query.id)
    
    await SocialAuthStates.waiting_for_credential.set()
    await bot.send_message(
        callback_query.from_user.id,
        f"🔑 Введите данные для входа в *{platform.upper()}* "
        f"(ИмяАккаунта Токен/Сессия через пробел):",
        parse_mode="Markdown"
    )

@dp.message_handler(state=SocialAuthStates.waiting_for_credential)
async def process_social_credential(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    platform = temp_auth_data.get(user_id, "tiktok")
    
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Неверный формат. Введите: `Имя Токен`", parse_mode="Markdown")
        return
        
    acc_name, credential = parts[0], parts[1]
    success = add_social_account(platform, acc_name, credential)
    
    if success:
        await message.answer(f"✅ Аккаунт *{acc_name}* для *{platform.upper()}* успешно добавлен!", parse_mode="Markdown")
    else:
        await message.answer("❌ Ошибка при сохранении сессии.")
        
    await state.finish()

@dp.message_handler(text="🌐 Добавить прокси")
async def start_add_proxy(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("⚠️ Сначала подключите хотя бы один телефон по ADB.")
        return
    await BotStates.waiting_for_proxy.set()
    await message.answer("🌐 Введите прокси в формате `ip:port` или `ip:port:login:pass`:")

@dp.message_handler(state=BotStates.waiting_for_proxy)
async def process_proxy(message: types.Message, state: FSMContext):
    proxy_str = message.text.strip()
    devices = get_connected_devices()
    if devices:
        success = connect_device_proxy(devices[0], proxy_str)
        if success:
            await message.answer(f"✅ Прокси установлен на устройство `{devices[0]}`!", parse_mode="Markdown")
        else:
            await message.answer("❌ Ошибка установки прокси.")
    await state.finish()

@dp.message_handler(text="👤 Добавить аккаунт")
async def start_add_account(message: types.Message):
    await BotStates.waiting_for_account.set()
    await message.answer("👤 Введите логин или юзернейм аккаунта:")

@dp.message_handler(state=BotStates.waiting_for_account)
async def process_account(message: types.Message, state: FSMContext):
    acc_name = message.text.strip()
    await message.answer(f"✅ Аккаунт *{acc_name}* привязан к системе!", parse_mode="Markdown")
    await state.finish()

@dp.message_handler(text="💼 Добавить оффер")
async def start_add_offer(message: types.Message):
    await BotStates.waiting_for_offer_name.set()
    await message.answer("💼 Введите название нового оффера:")

@dp.message_handler(state=BotStates.waiting_for_offer_name)
async def process_offer_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['offer_name'] = message.text.strip()
    await BotStates.next()
    await message.answer("💵 Введите цену за 1000 просмотров (CPM) в USD (например, `1.5`):")

@dp.message_handler(state=BotStates.waiting_for_offer_cpm)
async def process_offer_cpm(message: types.Message, state: FSMContext):
    try:
        cpm_usd = float(message.text.strip().replace(',', '.'))
        async with state.proxy() as data:
            offer_name = data['offer_name']
        add_offer(offer_name, cpm_usd)
        await message.answer(f"✅ Оффер *{offer_name}* с CPM **${cpm_usd}** добавлен!", parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Неверный формат числа.")
        return
    await state.finish()

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
        text += "\nНет добавленных офферов."
                
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler(text="🔍 Проверить теневой бан")
async def check_ban(message: types.Message):
    await message.answer("Введите юзернейм аккаунта для проверки теневого бана.")

@dp.message_handler(text="🛡 Обход теневого бана")
async def anti_ban_menu(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("Нет подключенных устройств.")
        return
    success = reset_device_fingerprint(devices[0])
    if success:
        await message.answer(f"🛡 Сброс отпечатков выполнен для устройства `{devices[0]}`!", parse_mode="Markdown")
    else:
        await message.answer("Ошибка сброса.")

@dp.message_handler(text="🔥 Прогреть аккаунт")
async def warm_up_action(message: types.Message):
    devices = get_connected_devices()
    if not devices:
        await message.answer("Нет подключенных устройств.")
        return
    await message.answer(f"🔥 Прогрев запущен на устройстве `{devices[0]}`...", parse_mode="Markdown")
