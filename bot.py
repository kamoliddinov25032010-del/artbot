import asyncio
import aiohttp
import random
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from deep_translator import GoogleTranslator
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
PREMIUM_PRICE = 150
OWNER_ID = 7695822564

user_counts = {}
premium_users = set()
user_styles = {}
user_sizes = {}
user_total = {}
user_bonus = {}
all_users = {}
blocked_users = set()

STYLES = {
    "realistic": "photorealistic, 4k, ultra detailed, sharp focus, professional",
    "anime": "anime style, manga, japanese art",
    "cartoon": "cartoon style, pixar, disney",
    "painting": "oil painting, artistic, renaissance style",
    "cyberpunk": "cyberpunk style, neon lights, futuristic city",
    "watercolor": "watercolor painting, soft colors, artistic",
    "sketch": "pencil sketch, hand drawn, black and white"
}

STYLE_NAMES = {
    "realistic": "📷 Fotorealistik",
    "anime": "🎌 Anime",
    "cartoon": "🎨 Multfilm",
    "painting": "🖼 Rasm",
    "cyberpunk": "🌆 Kiberpank",
    "watercolor": "🎨 Akvarel",
    "sketch": "✏️ Eskiz"
}

SIZES = {
    "square": "512x512",
    "horizontal": "768x512",
    "vertical": "512x768"
}

SIZE_NAMES = {
    "square": "⬛ Kvadrat",
    "horizontal": "🖥 Gorizontal",
    "vertical": "📱 Vertikal"
}

PROMPTS = {
    "🌅 Tabiat": [
        "beautiful sunset over mountains with golden sky",
        "magical forest with glowing fireflies at night",
        "ocean waves crashing on rocky shore at sunset",
        "cherry blossom tree in spring with pink petals",
        "snowy mountain peak with northern lights"
    ],
    "🏙 Shahar": [
        "futuristic city skyline at night with neon lights",
        "cozy cafe street in Paris with autumn leaves",
        "ancient japanese temple in misty morning",
        "modern dubai skyscrapers reflection in water",
        "vintage new york street in 1950s"
    ],
    "🐾 Hayvonlar": [
        "majestic lion portrait in golden savanna",
        "cute fox in snowy forest looking at camera",
        "colorful parrot in tropical rainforest",
        "white wolf howling at full moon",
        "playful dolphins jumping in ocean waves"
    ],
    "🧙 Fantaziya": [
        "magical dragon flying over medieval castle",
        "fairy tale enchanted forest with glowing mushrooms",
        "epic space battle between starships",
        "mystical mermaid underwater palace",
        "wizard casting colorful spells in dark forest"
    ],
    "🎭 Portret": [
        "elegant woman in red dress renaissance portrait",
        "brave warrior in ancient armor epic portrait",
        "mysterious witch with glowing eyes dark fantasy",
        "wise old wizard with long beard fantasy art",
        "beautiful princess in enchanted garden"
    ]
}

def main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🎨 Rasm yaratish"), KeyboardButton(text="💡 Tayyor promptlar")],
        [KeyboardButton(text="🎭 Uslub tanlash"), KeyboardButton(text="📏 O'lcham tanlash")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🎁 Referal"), KeyboardButton(text="⭐ Premium")]
    ], resize_keyboard=True)

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="📢 Hammaga xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⭐ Premium berish", callback_data="admin_give_premium")],
        [InlineKeyboardButton(text="🚫 Bloklash", callback_data="admin_block")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")]
    ])

def style_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"style_{key}")] for key, name in STYLE_NAMES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def size_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"size_{key}")] for key, name in SIZE_NAMES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def prompts_keyboard():
    buttons = [[InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}")] for cat in PROMPTS.keys()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text

def get_rank(total):
    if total >= 500: return "👑 Afsonaviy"
    elif total >= 100: return "💎 Usta"
    elif total >= 50: return "🥇 Tajribali"
    elif total >= 10: return "🥈 O'rta"
    else: return "🥉 Boshlang'ich"

async def create_image(message, prompt, user_id):
    style_key = user_styles.get(user_id, "realistic")
    style = STYLES[style_key]
    size = user_sizes.get(user_id, "square")
    w, h = SIZES[size].split("x")
    seed = random.randint(1, 99999)
    full_prompt = urllib.parse.quote(f"{translate_to_english(prompt)}, {style}")
    url = f"https://image.pollinations.ai/prompt/{full_prompt}?width={w}&height={h}&nologo=true&seed={seed}&model=flux"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                image_data = await response.read()
                await message.answer_photo(
                    photo=types.BufferedInputFile(image_data, filename="art.png"),
                    caption=f"🎨 {prompt}\n🎭 {STYLE_NAMES[style_key]} | 📏 {SIZE_NAMES[size]}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Qayta yaratish", callback_data=f"regen_{prompt[:50]}")],
                        [InlineKeyboardButton(text="🎭 Uslub", callback_data="change_style"),
                         InlineKeyboardButton(text="📏 O'lcham", callback_data="change_size")]
                    ])
                )
                return True
            return False

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    all_users[user_id] = message.from_user.first_name
    await message.answer(
        f"🎨 Salom {message.from_user.first_name}!\n\n"
        "Men Kamoliddinov Muhammadamin tomonidan yaratilgan kuchli san'at botman!\n\n"
        "Quyidagi tugmalardan foydalaning! 👇",
        reply_markup=main_keyboard()
    )

@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    total = len(all_users)
    premium = len(premium_users)
    images = sum(user_total.values())
    await message.answer(
        f"👨‍💼 Admin Panel\n\n"
        f"👥 Foydalanuvchilar: {total} ta\n"
        f"⭐ Premium: {premium} ta\n"
        f"🖼 Jami rasmlar: {images} ta\n"
        f"🚫 Bloklangan: {len(blocked_users)} ta",
        reply_markup=admin_keyboard()
    )

@dp.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    text = f"👥 Foydalanuvchilar ({len(all_users)} ta):\n\n"
    for uid, name in list(all_users.items())[:20]:
        total = user_total.get(uid, 0)
        is_premium = "⭐" if uid in premium_users else ""
        is_blocked = "🚫" if uid in blocked_users else ""
        text += f"{is_premium}{is_blocked} {name} — {total} rasm\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    total_images = sum(user_total.values())
    await callback.message.answer(
        f"📊 Bot statistikasi:\n\n"
        f"👥 Jami foydalanuvchilar: {len(all_users)} ta\n"
        f"⭐ Premium foydalanuvchilar: {len(premium_users)} ta\n"
        f"🖼 Jami yaratilgan rasmlar: {total_images} ta\n"
        f"🚫 Bloklangan: {len(blocked_users)} ta"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    await callback.message.answer("📢 Xabar yozing:\n\n/broadcast Xabaringiz")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_give_premium")
async def admin_give_premium(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    await callback.message.answer("⭐ Premium berish uchun:\n\n/givepremium 123456789")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_block")
async def admin_block_cb(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        return
    await callback.message.answer("🚫 Bloklash uchun:\n\n/block 123456789")
    await callback.answer()

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace("/broadcast ", "")
    sent = 0
    for uid in all_users:
        if uid not in blocked_users:
            try:
                await bot.send_message(uid, f"📢 {text}")
                sent += 1
            except:
                pass
    await message.answer(f"✅ {sent} ta foydalanuvchiga yuborildi!")

@dp.message(Command("givepremium"))
async def give_premium(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /givepremium 123456789")
        return
    uid = int(args[1])
    premium_users.add(uid)
    await message.answer(f"✅ {uid} ga premium berildi!")
    try:
        await bot.send_message(uid, "🎉 Sizga premium berildi! Cheksiz rasm yarating!")
    except:
        pass

@dp.message(Command("block"))
async def block_user(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /block 123456789")
        return
    uid = int(args[1])
    blocked_users.add(uid)
    await message.answer(f"🚫 {uid} bloklandi!")

@dp.message(Command("unblock"))
async def unblock_user(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /unblock 123456789")
        return
    uid = int(args[1])
    blocked_users.discard(uid)
    await message.answer(f"✅ {uid} blokdan chiqarildi!")

@dp.message(lambda m: m.text == "🎨 Rasm yaratish")
async def rasm_yaratish(message: types.Message):
    await message.answer("✍️ Xohlagan narsangizni yozing — o'zbek yoki inglizcha!\n\nMasalan: tog'lar va quyosh")

@dp.message(lambda m: m.text == "💡 Tayyor promptlar")
async def tayyor_promptlar(message: types.Message):
    await message.answer("💡 Kategoriya tanlang:", reply_markup=prompts_keyboard())

@dp.message(lambda m: m.text == "🎭 Uslub tanlash")
async def uslub_tanlash(message: types.Message):
    await message.answer("🎭 Uslub tanlang:", reply_markup=style_keyboard())

@dp.message(lambda m: m.text == "📏 O'lcham tanlash")
async def olcham_tanlash(message: types.Message):
    await message.answer("📏 O'lcham tanlang:", reply_markup=size_keyboard())

@dp.message(lambda m: m.text == "📊 Statistika")
async def statistika(message: types.Message):
    user_id = message.from_user.id
    total = user_total.get(user_id, 0)
    bonus = user_bonus.get(user_id, 0)
    await message.answer(
        f"📊 Sizning statistikangiz:\n\n"
        f"🏅 Daraja: {get_rank(total)}\n"
        f"🖼 Jami rasmlar: {total} ta\n"
        f"🎁 Bonus rasmlar: {bonus} ta"
    )

@dp.message(lambda m: m.text == "🏆 Reyting")
async def reyting(message: types.Message):
    if not user_total:
        await message.answer("🏆 Hali hech kim rasm yaratmagan!")
        return
    sorted_users = sorted(user_total.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 Eng faol foydalanuvchilar:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, count) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = all_users.get(uid, "Foydalanuvchi")
        text += f"{medal} {name} — {count} ta rasm\n"
    await message.answer(text)

@dp.message(lambda m: m.text == "🎁 Referal")
async def referal(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    bonus = user_bonus.get(user_id, 0)
    await message.answer(
        f"🎁 Sizning referal linkingiz:\n{link}\n\n"
        f"Do'stingiz shu link orqali kirsa:\n"
        f"✅ Siz +3 bonus rasm\n"
        f"✅ Do'stingiz +3 bonus rasm\n\n"
        f"💰 Bonuslaringiz: {bonus} ta"
    )

@dp.message(lambda m: m.text == "⭐ Premium")
async def premium_btn(message: types.Message):
    await bot.send_invoice(chat_id=message.chat.id, title="⭐ Premium obuna", description="Cheksiz rasm yaratish!", payload="premium", currency="XTR", prices=[LabeledPrice(label="Premium", amount=PREMIUM_PRICE)])

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def category_selected(callback: CallbackQuery):
    cat = callback.data.replace("cat_", "")
    prompts = PROMPTS.get(cat, [])
    buttons = [[InlineKeyboardButton(text=f"🎨 {p[:40]}", callback_data=f"prompt_{p[:50]}")] for p in prompts]
    await callback.message.answer(f"{cat} promptlari:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("prompt_"))
async def prompt_selected(callback: CallbackQuery):
    prompt = callback.data.replace("prompt_", "")
    await callback.answer("🎨 Yaratilmoqda...")
    await callback.message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    await create_image(callback.message, prompt, callback.from_user.id)

@dp.callback_query(lambda c: c.data.startswith("style_"))
async def style_selected(callback: CallbackQuery):
    style = callback.data.replace("style_", "")
    user_styles[callback.from_user.id] = style
    await callback.answer(f"{STYLE_NAMES[style]} tanlandi!")
    await callback.message.answer(f"✅ {STYLE_NAMES[style]} uslubi tanlandi!")

@dp.callback_query(lambda c: c.data.startswith("size_"))
async def size_selected(callback: CallbackQuery):
    size = callback.data.replace("size_", "")
    user_sizes[callback.from_user.id] = size
    await callback.answer(f"{SIZE_NAMES[size]} tanlandi!")
    await callback.message.answer(f"✅ {SIZE_NAMES[size]} o'lchami tanlandi!")

@dp.callback_query(lambda c: c.data == "change_style")
async def change_style(callback: CallbackQuery):
    await callback.message.answer("🎭 Uslub tanlang:", reply_markup=style_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "change_size")
async def change_size(callback: CallbackQuery):
    await callback.message.answer("📏 O'lcham tanlang:", reply_markup=size_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("regen_"))
async def regenerate(callback: CallbackQuery):
    prompt = callback.data.replace("regen_", "")
    await callback.answer("🔄 Qayta yaratilmoqda...")
    await callback.message.answer("🎨 Yangi rasm yaratilmoqda...")
    await create_image(callback.message, prompt, callback.from_user.id)

@dp.message(Command("premium"))
async def premium(message: types.Message):
    await bot.send_invoice(chat_id=message.chat.id, title="⭐ Premium obuna", description="Cheksiz rasm yaratish!", payload="premium", currency="XTR", prices=[LabeledPrice(label="Premium", amount=PREMIUM_PRICE)])

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(lambda m: m.successful_payment is not None)
async def payment_done(message: types.Message):
    premium_users.add(message.from_user.id)
    await message.answer("🎉 Premium faollashdi! Cheksiz rasm yarating!")

@dp.message(lambda m: m.photo is not None)
async def analyze_image(message: types.Message):
    await message.answer("🖼 Rasm qabul qilindi!\n\n✏️ Rasm tahrirlash tez orada!")

@dp.message()
async def generate_image(message: types.Message):
    user_id = message.from_user.id
    all_users[user_id] = message.from_user.first_name
    if user_id in blocked_users:
        await message.answer("🚫 Siz bloklangansiz!")
        return
    if user_id not in user_counts:
        user_counts[user_id] = 0
    is_owner = user_id == OWNER_ID
    is_premium = user_id in premium_users
    count = user_counts.get(user_id, 0)
    bonus = user_bonus.get(user_id, 0)
    if not is_owner and not is_premium and count >= FREE_LIMIT and bonus <= 0:
        await message.answer("⭐ Limit tugadi! Premium: /premium\n🎁 Bonus uchun: /ref")
        return
    await message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    success = await create_image(message, message.text, user_id)
    if success:
        user_total[user_id] = user_total.get(user_id, 0) + 1
        if not is_owner and not is_premium:
            if bonus > 0:
                user_bonus[user_id] = bonus - 1
            else:
                user_counts[user_id] = count + 1
            remaining = FREE_LIMIT - user_counts.get(user_id, 0) + user_bonus.get(user_id, 0)
            await message.answer(f"💡 Bugun yana {max(0, remaining)} ta rasm qoldi!")
        total = user_total[user_id]
        if total % 10 == 0:
            user_bonus[user_id] = user_bonus.get(user_id, 0) + 1
            await message.answer(f"🎉 {total} ta rasm! +1 bonus!\n{get_rank(total)} darajasi!")
    else:
        await message.answer("❌ Xatolik! Qayta urinib ko'ring.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
