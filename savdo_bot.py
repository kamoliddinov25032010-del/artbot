#!/usr/bin/env python3
"""
Savdo Kalkulyator Telegram Bot
O'zbek, Rus, Ingliz tillarida ishlaydi
Funksiyalar: narx hisoblash, katalog, mijozlar, statistika, hisobot, chek
"""

import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)

# ─── TOKEN ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8921064895:AAFXrnhTdjP8DhFZ-1D5rFrpZjY5JF78L6c"

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── MA'LUMOTLAR SAQLASH (JSON fayl) ─────────────────────────────────────────
DATA_FILE = "savdo_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"katalog": {}, "mijozlar": {}, "savdolar": [], "sozlamalar": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── TARJIMALAR ───────────────────────────────────────────────────────────────
LANGS = {
    "uz": {
        "welcome": "👋 Savdo Kalkulyator Botiga xush kelibsiz!\n\nQuyidagi menyudan birini tanlang:",
        "menu": "📋 Asosiy menyu",
        "btn_calc": "🧮 Hisoblash",
        "btn_katalog": "📦 Katalog",
        "btn_mijoz": "👥 Mijozlar",
        "btn_stat": "📊 Statistika",
        "btn_lang": "🌐 Til",
        "btn_help": "❓ Yordam",
        "enter_product": "Mahsulot nomini kiriting:",
        "enter_price": "Narxini kiriting (so'm):",
        "enter_qty": "Miqdorini kiriting:",
        "enter_discount": "Chegirma foizini kiriting (0-100), yoki 0:",
        "receipt": "🧾 CHEK",
        "total": "JAMI",
        "discount": "Chegirma",
        "subtotal": "Oraliq jami",
        "add_more": "➕ Mahsulot qo'shish",
        "finish": "✅ Hisobni yakunlash",
        "cancel": "❌ Bekor qilish",
        "new_calc": "🔄 Yangi hisob",
        "stat_title": "📊 Statistika",
        "no_data": "Ma'lumot yo'q",
        "katalog_empty": "Katalog bo'sh. /katalog_qosh buyrug'i bilan qo'shing.",
        "help_text": (
            "📖 Buyruqlar ro'yxati:\n\n"
            "/start — Boshlamoq\n"
            "/hisob — Yangi hisoblash\n"
            "/katalog — Mahsulotlar katalogi\n"
            "/katalog_qosh — Katalogga qo'shish\n"
            "/mijozlar — Mijozlar ro'yxati\n"
            "/mijoz_qosh — Yangi mijoz\n"
            "/statistika — Savdo statistikasi\n"
            "/til — Tilni o'zgartirish\n"
            "/yordam — Yordam"
        ),
        "saved": "✅ Saqlandi!",
        "currency": "so'm",
        "lang_changed": "Til o'zgartirildi: O'zbek 🇺🇿",
        "clients_title": "👥 Mijozlar ro'yxati",
        "client_added": "✅ Mijoz qo'shildi!",
        "enter_client_name": "Mijoz ismini kiriting:",
        "enter_client_phone": "Telefon raqamini kiriting:",
        "cat_added": "✅ Katalogga qo'shildi!",
        "enter_cat_name": "Mahsulot nomini kiriting:",
        "enter_cat_price": "Mahsulot narxini kiriting:",
        "select_from_cat": "Katalogdan mahsulot tanlang:",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в Калькулятор продаж!\n\nВыберите пункт меню:",
        "menu": "📋 Главное меню",
        "btn_calc": "🧮 Расчёт",
        "btn_katalog": "📦 Каталог",
        "btn_mijoz": "👥 Клиенты",
        "btn_stat": "📊 Статистика",
        "btn_lang": "🌐 Язык",
        "btn_help": "❓ Помощь",
        "enter_product": "Введите название товара:",
        "enter_price": "Введите цену (сум):",
        "enter_qty": "Введите количество:",
        "enter_discount": "Введите скидку % (0-100), или 0:",
        "receipt": "🧾 ЧЕК",
        "total": "ИТОГО",
        "discount": "Скидка",
        "subtotal": "Подытог",
        "add_more": "➕ Добавить товар",
        "finish": "✅ Завершить расчёт",
        "cancel": "❌ Отмена",
        "new_calc": "🔄 Новый расчёт",
        "stat_title": "📊 Статистика",
        "no_data": "Нет данных",
        "katalog_empty": "Каталог пуст. Добавьте через /katalog_qosh.",
        "help_text": (
            "📖 Список команд:\n\n"
            "/start — Начать\n"
            "/hisob — Новый расчёт\n"
            "/katalog — Каталог товаров\n"
            "/katalog_qosh — Добавить в каталог\n"
            "/mijozlar — Список клиентов\n"
            "/mijoz_qosh — Новый клиент\n"
            "/statistika — Статистика продаж\n"
            "/til — Изменить язык\n"
            "/yordam — Помощь"
        ),
        "saved": "✅ Сохранено!",
        "currency": "сум",
        "lang_changed": "Язык изменён: Русский 🇷🇺",
        "clients_title": "👥 Список клиентов",
        "client_added": "✅ Клиент добавлен!",
        "enter_client_name": "Введите имя клиента:",
        "enter_client_phone": "Введите номер телефона:",
        "cat_added": "✅ Добавлено в каталог!",
        "enter_cat_name": "Введите название товара:",
        "enter_cat_price": "Введите цену товара:",
        "select_from_cat": "Выберите товар из каталога:",
    },
    "en": {
        "welcome": "👋 Welcome to Sales Calculator Bot!\n\nChoose from the menu:",
        "menu": "📋 Main menu",
        "btn_calc": "🧮 Calculate",
        "btn_katalog": "📦 Catalog",
        "btn_mijoz": "👥 Clients",
        "btn_stat": "📊 Statistics",
        "btn_lang": "🌐 Language",
        "btn_help": "❓ Help",
        "enter_product": "Enter product name:",
        "enter_price": "Enter price (UZS):",
        "enter_qty": "Enter quantity:",
        "enter_discount": "Enter discount % (0-100), or 0:",
        "receipt": "🧾 RECEIPT",
        "total": "TOTAL",
        "discount": "Discount",
        "subtotal": "Subtotal",
        "add_more": "➕ Add product",
        "finish": "✅ Finish",
        "cancel": "❌ Cancel",
        "new_calc": "🔄 New calculation",
        "stat_title": "📊 Statistics",
        "no_data": "No data yet",
        "katalog_empty": "Catalog is empty. Add via /katalog_qosh.",
        "help_text": (
            "📖 Commands:\n\n"
            "/start — Start\n"
            "/hisob — New calculation\n"
            "/katalog — Product catalog\n"
            "/katalog_qosh — Add to catalog\n"
            "/mijozlar — Client list\n"
            "/mijoz_qosh — New client\n"
            "/statistika — Sales statistics\n"
            "/til — Change language\n"
            "/yordam — Help"
        ),
        "saved": "✅ Saved!",
        "currency": "UZS",
        "lang_changed": "Language changed: English 🇬🇧",
        "clients_title": "👥 Client list",
        "client_added": "✅ Client added!",
        "enter_client_name": "Enter client name:",
        "enter_client_phone": "Enter phone number:",
        "cat_added": "✅ Added to catalog!",
        "enter_cat_name": "Enter product name:",
        "enter_cat_price": "Enter product price:",
        "select_from_cat": "Select product from catalog:",
    }
}

def t(uid, key):
    data = load_data()
    lang = data["sozlamalar"].get(str(uid), {}).get("til", "uz")
    return LANGS.get(lang, LANGS["uz"]).get(key, key)

def get_lang(uid):
    data = load_data()
    return data["sozlamalar"].get(str(uid), {}).get("til", "uz")

def fmt(n):
    return f"{int(n):,}".replace(",", " ")

# ─── CONVERSATION STATES ──────────────────────────────────────────────────────
(
    CALC_PRODUCT, CALC_PRICE, CALC_QTY, CALC_DISCOUNT,
    CAT_NAME, CAT_PRICE,
    CLIENT_NAME, CLIENT_PHONE
) = range(8)

# ─── MAIN MENU ────────────────────────────────────────────────────────────────
def main_keyboard(uid):
    return ReplyKeyboardMarkup([
        [t(uid, "btn_calc"), t(uid, "btn_katalog")],
        [t(uid, "btn_mijoz"), t(uid, "btn_stat")],
        [t(uid, "btn_lang"), t(uid, "btn_help")],
    ], resize_keyboard=True)

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        t(uid, "welcome"),
        reply_markup=main_keyboard(uid)
    )

# ─── /yordam ──────────────────────────────────────────────────────────────────
async def yordam(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "help_text"))

# ─── TIL ──────────────────────────────────────────────────────────────────────
async def til(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])
    await update.message.reply_text("🌐 Tilni tanlang / Выберите язык / Choose language:", reply_markup=kb)

async def lang_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang_code = query.data.split("_")[1]
    data = load_data()
    if str(uid) not in data["sozlamalar"]:
        data["sozlamalar"][str(uid)] = {}
    data["sozlamalar"][str(uid)]["til"] = lang_code
    save_data(data)
    await query.edit_message_text(t(uid, "lang_changed"))

# ─── HISOBLASH ────────────────────────────────────────────────────────────────
async def hisob_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ctx.user_data["items"] = []
    ctx.user_data["calc_step"] = "product"
    await update.message.reply_text(t(uid, "enter_product"))
    return CALC_PRODUCT

async def calc_product(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ctx.user_data["current_name"] = update.message.text
    await update.message.reply_text(t(uid, "enter_price"))
    return CALC_PRICE

async def calc_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        price = float(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["current_price"] = price
        await update.message.reply_text(t(uid, "enter_qty"))
        return CALC_QTY
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return CALC_PRICE

async def calc_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        qty = int(update.message.text)
        ctx.user_data["current_qty"] = qty
        await update.message.reply_text(t(uid, "enter_discount"))
        return CALC_DISCOUNT
    except ValueError:
        await update.message.reply_text("❌ Butun son kiriting!")
        return CALC_QTY

async def calc_discount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        disc = float(update.message.text)
        name = ctx.user_data["current_name"]
        price = ctx.user_data["current_price"]
        qty = ctx.user_data["current_qty"]
        ctx.user_data["items"].append({"name": name, "price": price, "qty": qty, "disc": disc})

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(uid, "add_more"), callback_data="calc_add")],
            [InlineKeyboardButton(t(uid, "finish"), callback_data="calc_finish")],
            [InlineKeyboardButton(t(uid, "cancel"), callback_data="calc_cancel")],
        ])
        items = ctx.user_data["items"]
        lines = ""
        sub = 0
        for it in items:
            line = it["price"] * it["qty"]
            disc_amt = line * it["disc"] / 100
            net = line - disc_amt
            sub += net
            lines += f"• {it['name']}: {fmt(it['price'])} × {it['qty']}"
            if it["disc"] > 0:
                lines += f" (-{it['disc']}%)"
            lines += f" = {fmt(net)} {t(uid, 'currency')}\n"

        msg = f"🛒 Joriy hisob:\n\n{lines}\n💰 {t(uid, 'subtotal')}: {fmt(sub)} {t(uid, 'currency')}"
        await update.message.reply_text(msg, reply_markup=kb)
        return CALC_DISCOUNT
    except ValueError:
        await update.message.reply_text("❌ 0-100 oralig'ida raqam kiriting!")
        return CALC_DISCOUNT

async def calc_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "calc_add":
        await query.message.reply_text(t(uid, "enter_product"))
        return CALC_PRODUCT

    elif query.data == "calc_finish":
        items = ctx.user_data.get("items", [])
        if not items:
            await query.edit_message_text("Hech narsa yo'q!")
            return ConversationHandler.END

        subtotal = sum(it["price"] * it["qty"] for it in items)
        total_disc = sum(it["price"] * it["qty"] * it["disc"] / 100 for it in items)
        total = subtotal - total_disc
        lang = get_lang(uid)
        cur = LANGS[lang]["currency"]

        lines = f"{'─'*30}\n"
        lines += f"🧾 {t(uid, 'receipt')}\n"
        lines += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        lines += f"{'─'*30}\n\n"

        for it in items:
            line = it["price"] * it["qty"]
            disc_amt = line * it["disc"] / 100
            net = line - disc_amt
            lines += f"📌 {it['name']}\n"
            lines += f"   {fmt(it['price'])} × {it['qty']} = {fmt(line)} {cur}\n"
            if it["disc"] > 0:
                lines += f"   🏷 -{it['disc']}% = -{fmt(disc_amt)} {cur}\n"
                lines += f"   ✅ {fmt(net)} {cur}\n"
            lines += "\n"

        lines += f"{'─'*30}\n"
        lines += f"📦 {t(uid, 'subtotal')}: {fmt(subtotal)} {cur}\n"
        if total_disc > 0:
            lines += f"🏷 {t(uid, 'discount')}: -{fmt(total_disc)} {cur}\n"
        lines += f"💰 {t(uid, 'total')}: {fmt(total)} {cur}\n"
        lines += f"{'─'*30}"

        # Statistikaga saqlash
        data = load_data()
        data["savdolar"].append({
            "sana": datetime.now().isoformat(),
            "uid": uid,
            "jami": total,
            "chegirma": total_disc,
            "mahsulotlar": len(items)
        })
        save_data(data)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(uid, "new_calc"), callback_data="calc_new")]
        ])
        await query.message.reply_text(lines, reply_markup=kb)
        return ConversationHandler.END

    elif query.data == "calc_cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END

    elif query.data == "calc_new":
        ctx.user_data["items"] = []
        await query.message.reply_text(t(uid, "enter_product"))
        return CALC_PRODUCT

# ─── KATALOG ──────────────────────────────────────────────────────────────────
async def katalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    kat = data.get("katalog", {})
    if not kat:
        await update.message.reply_text(t(uid, "katalog_empty"))
        return
    lang = get_lang(uid)
    cur = LANGS[lang]["currency"]
    lines = "📦 Katalog:\n\n"
    for name, info in kat.items():
        lines += f"• {name}: {fmt(info['narx'])} {cur}\n"
    await update.message.reply_text(lines)

async def katalog_qosh_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "enter_cat_name"))
    return CAT_NAME

async def cat_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["cat_name"] = update.message.text
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "enter_cat_price"))
    return CAT_PRICE

async def cat_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        price = float(update.message.text.replace(" ", "").replace(",", ""))
        data = load_data()
        data["katalog"][ctx.user_data["cat_name"]] = {"narx": price}
        save_data(data)
        await update.message.reply_text(t(uid, "cat_added"))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return CAT_PRICE

# ─── MIJOZLAR ────────────────────────────────────────────────────────────────
async def mijozlar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    mij = data.get("mijozlar", {})
    if not mij:
        await update.message.reply_text(t(uid, "no_data"))
        return
    lines = f"{t(uid, 'clients_title')}:\n\n"
    for name, info in mij.items():
        lines += f"👤 {name} — 📞 {info.get('tel', '—')}\n"
    await update.message.reply_text(lines)

async def mijoz_qosh_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "enter_client_name"))
    return CLIENT_NAME

async def client_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["client_name"] = update.message.text
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "enter_client_phone"))
    return CLIENT_PHONE

async def client_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    data["mijozlar"][ctx.user_data["client_name"]] = {"tel": update.message.text}
    save_data(data)
    await update.message.reply_text(t(uid, "client_added"))
    return ConversationHandler.END

# ─── STATISTIKA ───────────────────────────────────────────────────────────────
async def statistika(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    savdolar = data.get("savdolar", [])
    if not savdolar:
        await update.message.reply_text(t(uid, "no_data"))
        return

    lang = get_lang(uid)
    cur = LANGS[lang]["currency"]
    jami = sum(s["jami"] for s in savdolar)
    chegirma = sum(s["chegirma"] for s in savdolar)
    mahsulotlar = sum(s["mahsulotlar"] for s in savdolar)
    soni = len(savdolar)

    # Bugungi savdolar
    bugun = datetime.now().date().isoformat()
    bugungi = [s for s in savdolar if s["sana"][:10] == bugun]
    bugun_jami = sum(s["jami"] for s in bugungi)

    msg = (
        f"📊 {t(uid, 'stat_title')}\n"
        f"{'─'*28}\n\n"
        f"📅 Bugun: {fmt(bugun_jami)} {cur} ({len(bugungi)} ta savdo)\n\n"
        f"📦 Jami savdolar soni: {soni}\n"
        f"💰 Jami tushum: {fmt(jami)} {cur}\n"
        f"🏷 Berilgan chegirmalar: {fmt(chegirma)} {cur}\n"
        f"🛒 Sotilgan mahsulotlar: {mahsulotlar} ta\n"
        f"💵 O'rtacha savdo: {fmt(jami/soni if soni else 0)} {cur}\n"
        f"{'─'*28}\n"
        f"📅 Oxirgi savdo: {savdolar[-1]['sana'][:16].replace('T', ' ')}"
    )
    await update.message.reply_text(msg)

# ─── MENYU TUGMALARI ──────────────────────────────────────────────────────────
async def menu_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    for lang_code, tr in LANGS.items():
        if text == tr["btn_stat"]:
            return await statistika(update, ctx)
        if text == tr["btn_katalog"]:
            return await katalog(update, ctx)
        if text == tr["btn_mijoz"]:
            return await mijozlar(update, ctx)
        if text == tr["btn_lang"]:
            return await til(update, ctx)
        if text == tr["btn_help"]:
            return await yordam(update, ctx)
        if text == tr["btn_calc"]:
            return await hisob_start(update, ctx)

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_keyboard(uid))
    return ConversationHandler.END

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Hisoblash suhbati
    calc_conv = ConversationHandler(
        entry_points=[
            CommandHandler("hisob", hisob_start),
        ],
        states={
            CALC_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_product)],
            CALC_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_price)],
            CALC_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, calc_qty)],
            CALC_DISCOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, calc_discount),
                CallbackQueryHandler(calc_callback, pattern="^calc_"),
            ],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
    )

    # Katalog qo'shish suhbati
    cat_conv = ConversationHandler(
        entry_points=[CommandHandler("katalog_qosh", katalog_qosh_start)],
        states={
            CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_name)],
            CAT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_price)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
    )

    # Mijoz qo'shish suhbati
    client_conv = ConversationHandler(
        entry_points=[CommandHandler("mijoz_qosh", mijoz_qosh_start)],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CLIENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_phone)],
        },
        fallbacks=[CommandHandler("bekor", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(CommandHandler("til", til))
    app.add_handler(CommandHandler("katalog", katalog))
    app.add_handler(CommandHandler("mijozlar", mijozlar))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(calc_conv)
    app.add_handler(cat_conv)
    app.add_handler(client_conv)
    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(calc_callback, pattern="^calc_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
