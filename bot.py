import asyncio
import aiohttp
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from deep_translator import GoogleTranslator
import os
import urllib.parse

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
PREMIUM_PRICE = 50
OWNER_ID = 7695822564

user_counts = {}
premium_users = set()
user_styles = {}
user_total = {}
user_bonus = {}
user_streak = {}
user_last_day = {}
referrals = {}

STYLES = {
    "realistic": "photorealistic, 4k, ultra detailed",
    "anime": "anime style, manga, japanese art",
    "cartoon": "cartoon style, pixar, disney",
    "painting": "oil painting, artistic, renaissance style"
}

STYLE_NAMES = {
    "realistic": "📷 Fotorealistik",
    "anime": "🎌 Anime",
    "cartoon": "🎨 Multfilm",
    "painting": "🖼 Rasm"
}

def style_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"style_{key}")] for key, name in STYLE_NAMES.items()]
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
    english_prompt = translate_to_english(prompt)
    style_key = user_styles.get(user_id, "realistic")
    style = STYLES[style_key]
    seed = random.randint(1, 99999)
    full_prompt = urllib.parse.quote(f"{english_prompt}, {style}")
    url = f"https://image.pollinations.ai/prompt/{full_prompt}?width=512&height=512&nologo=true&seed={seed}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                image_data = await response.read()
                await message.answer_photo(
                    photo=types.BufferedInputFile(image_data, filename="art.png"),
                    caption=f"🎨 {prompt}\n🎭 Uslub: {STYLE_NAMES[style_key]}",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Qayta yaratish", callback_data=f"regen_{prompt[:50]}")],
                        [InlineKeyboardButton(text="🎭 Uslub", callback_data="change_style")]
                    ])
                )
                return True
            return False

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1:
        ref_id = int(args[1]) if args[1].isdigit() else None
        if ref_id and ref_id != user_id and ref_id not in referrals.get(user_id, []):
            if user_id not in referrals:
                referrals[user_id] = []
            referrals[user_id].append(ref_id)
            user_bonus[user_id] = user_bonus.get(user_id, 0) + 3
            user_bonus[ref_id] = user_bonus.get(ref_id, 0) + 3
            await bot.send_message(ref_id, f"🎁 Do'stingiz botga kirdi! +3 bonus rasm oldingiz!")
    await message.answer(
        f"🎨 Salom {message.from_user.first_name}! Men kuchli san'at botman!\n\n"
        "🖼 Rasm yaratish — o'zbek yoki inglizcha yozing\n"
        "🎭 Uslub — /style\n"
        "📊 Statistika — /stats\n"
        "🏆 Reyting — /top\n"
        "🎁 Referal — /ref\n"
        "⭐ Premium — /premium\n\n"
        "Boshlang! 🚀"
    )

@dp.message(Command("stats"))
async def stats(message: types.Message):
    user_id = message.from_user.id
    total = user_total.get(user_id, 0)
    bonus = user_bonus.get(user_id, 0)
    streak = user_streak.get(user_id, 0)
    rank = get_rank(total)
    await message.answer(
        f"📊 Sizning statistikangiz:\n\n"
        f"🏅 Daraja: {rank}\n"
        f"🖼 Jami rasmlar: {total} ta\n"
        f"🎁 Bonus rasmlar: {bonus} ta\n"
        f"🔥 Ketma-ket kunlar: {streak} kun\n\n"
        f"Keyingi daraja uchun ko'proq rasm yarating!"
    )

@dp.message(Command("top"))
async def top(message: types.Message):
    if not user_total:
        await message.answer("🏆 Hali hech kim rasm yaratmagan!")
        return
    sorted_users = sorted(user_total.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 Eng faol foydalanuvchilar:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, count) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = "Foydalanuvchi"
        text += f"{medal} {name} — {count} ta rasm\n"
    await message.answer(text)

@dp.message(Command("ref"))
async def ref(message: types.Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    bonus = user_bonus.get(user_id, 0)
    await message.answer(
        f"🎁 Sizning referal linkingiz:\n{link}\n\n"
        f"Do'stingiz shu link orqali kirsa:\n"
        f"✅ Siz +3 bonus rasm olasiz\n"
        f"✅ Do'stingiz ham +3 bonus rasm oladi\n\n"
        f"💰 Hozirgi bonuslaringiz: {bonus} ta"
    )

@dp.message(Command("style"))
async def style_cmd(message: types.Message):
    await message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())

@dp.callback_query(lambda c: c.data.startswith("style_"))
async def style_selected(callback: CallbackQuery):
    style = callback.data.replace("style_", "")
    user_styles[callback.from_user.id] = style
    await callback.answer(f"{STYLE_NAMES[style]} tanlandi!")
    await callback.message.answer(f"✅ {STYLE_NAMES[style]} uslubi tanlandi!")

@dp.callback_query(lambda c: c.data == "change_style")
async def change_style(callback: CallbackQuery):
    await callback.message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())
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
    if user_id not in user_counts:
        user_counts[user_id] = 0
    if user_id not in user_total:
        user_total[user_id] = 0
    is_owner = user_id == OWNER_ID
    bonus = user_bonus.get(user_id, 0)
    available = user_id in premium_users or is_owner or user_counts[user_id] < FREE_LIMIT or bonus > 0
    if not available:
        await message.answer("⭐ Limit tugadi! Premium: /premium\n🎁 Referal: /ref")
        return
    await message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    success = await create_image(message, message.text, user_id)
    if success:
        user_total[user_id] += 1
        if not is_owner and user_id not in premium_users:
            if bonus > 0:
                user_bonus[user_id] -= 1
            else:
                user_counts[user_id] += 1
            remaining = FREE_LIMIT - user_counts[user_id] + user_bonus.get(user_id, 0)
            if remaining >= 0:
                await message.answer(f"💡 Bugun yana {remaining} ta rasm qoldi!")
        total = user_total[user_id]
        if total % 10 == 0:
            user_bonus[user_id] = user_bonus.get(user_id, 0) + 1
            await message.answer(f"🎉 {total} ta rasm yaratdingiz! +1 bonus rasm!\n{get_rank(total)} darajasiga erishdingiz!")
    else:
        await message.answer("❌ Xatolik! Qayta urinib ko'ring.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
