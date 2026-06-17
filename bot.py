import asyncio
import aiohttp
import random
import json
import os
import urllib.parse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from deep_translator import GoogleTranslator

BOT_TOKEN = os.environ["BOT_TOKEN"]
DATA_FILE = "data.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
PREMIUM_PRICE = 50
OWNER_ID = 7695822564

STYLES = {
    "realistic": "photorealistic, 4k, ultra detailed, highly detailed, sharp focus, professional",
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

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"counts": {}, "total": {}, "bonus": {}, "premium": [], "styles": {}, "referrals": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_rank(total):
    if total >= 500: return "👑 Afsonaviy"
    elif total >= 100: return "💎 Usta"
    elif total >= 50: return "🥇 Tajribali"
    elif total >= 10: return "🥈 O'rta"
    else: return "🥉 Boshlang'ich"

def style_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"style_{key}")] for key, name in STYLE_NAMES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text

async def create_image(message, prompt, user_id):
    data = load_data()
    style_key = data["styles"].get(str(user_id), "realistic")
    style = STYLES[style_key]
    seed = random.randint(1, 99999)
    full_prompt = urllib.parse.quote(f"{translate_to_english(prompt)}, {style}")
    url = f"https://image.pollinations.ai/prompt/{full_prompt}?width=512&height=512&nologo=true&seed={seed}&model=flux"
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
    user_id = str(message.from_user.id)
    data = load_data()
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = args[1]
        if ref_id != user_id and user_id not in data["referrals"].get(ref_id, []):
            if ref_id not in data["referrals"]:
                data["referrals"][ref_id] = []
            data["referrals"][ref_id].append(user_id)
            data["bonus"][user_id] = data["bonus"].get(user_id, 0) + 3
            data["bonus"][ref_id] = data["bonus"].get(ref_id, 0) + 3
            save_data(data)
            await bot.send_message(int(ref_id), "🎁 Do'stingiz botga kirdi! +3 bonus rasm oldingiz!")
    await message.answer(
        f"🎨 Salom {message.from_user.first_name}!\n\n"
        "Men Kamoliddinov Muhammadamin tomonidan yaratilgan kuchli san'at botman!\n\n"
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
    user_id = str(message.from_user.id)
    data = load_data()
    total = data["total"].get(user_id, 0)
    bonus = data["bonus"].get(user_id, 0)
    await message.answer(
        f"📊 Sizning statistikangiz:\n\n"
        f"🏅 Daraja: {get_rank(total)}\n"
        f"🖼 Jami rasmlar: {total} ta\n"
        f"🎁 Bonus rasmlar: {bonus} ta\n\n"
        f"Keyingi daraja uchun ko'proq rasm yarating!"
    )

@dp.message(Command("top"))
async def top(message: types.Message):
    data = load_data()
    if not data["total"]:
        await message.answer("🏆 Hali hech kim rasm yaratmagan!")
        return
    sorted_users = sorted(data["total"].items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 Eng faol foydalanuvchilar:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, count) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        try:
            user = await bot.get_chat(int(uid))
            name = user.first_name
        except:
            name = "Foydalanuvchi"
        text += f"{medal} {name} — {count} ta rasm\n"
    await message.answer(text)

@dp.message(Command("ref"))
async def ref(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_id}"
    bonus = data["bonus"].get(user_id, 0)
    await message.answer(
        f"🎁 Sizning referal linkingiz:\n{link}\n\n"
        f"Do'stingiz shu link orqali kirsa:\n"
        f"✅ Siz +3 bonus rasm\n"
        f"✅ Do'stingiz +3 bonus rasm\n\n"
        f"💰 Hozirgi bonuslaringiz: {bonus} ta"
    )

@dp.message(Command("style"))
async def style_cmd(message: types.Message):
    await message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())

@dp.callback_query(lambda c: c.data.startswith("style_"))
async def style_selected(callback: CallbackQuery):
    style = callback.data.replace("style_", "")
    data = load_data()
    data["styles"][str(callback.from_user.id)] = style
    save_data(data)
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
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data["premium"]:
        data["premium"].append(user_id)
    save_data(data)
    await message.answer("🎉 Premium faollashdi! Cheksiz rasm yarating!")

@dp.message(lambda m: m.photo is not None)
async def analyze_image(message: types.Message):
    await message.answer("🖼 Rasm qabul qilindi!\n\n✏️ Rasm tahrirlash tez orada!")

@dp.message()
async def generate_image(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    is_owner = int(user_id) == OWNER_ID
    is_premium = user_id in data["premium"]
    count = data["counts"].get(user_id, 0)
    bonus = data["bonus"].get(user_id, 0)
    if not is_owner and not is_premium and count >= FREE_LIMIT and bonus <= 0:
        await message.answer("⭐ Limit tugadi! Premium: /premium\n🎁 Bonus uchun: /ref")
        return
    await message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    success = await create_image(message, message.text, int(user_id))
    if success:
        data["total"][user_id] = data["total"].get(user_id, 0) + 1
        if not is_owner and not is_premium:
            if bonus > 0:
                data["bonus"][user_id] -= 1
            else:
                data["counts"][user_id] = count + 1
            remaining = FREE_LIMIT - data["counts"].get(user_id, 0) + data["bonus"].get(user_id, 0)
            await message.answer(f"💡 Bugun yana {max(0, remaining)} ta rasm qoldi!")
        total = data["total"][user_id]
        if total % 10 == 0:
            data["bonus"][user_id] = data["bonus"].get(user_id, 0) + 1
            await message.answer(f"🎉 {total} ta rasm! +1 bonus!\n{get_rank(total)} darajasi!")
        save_data(data)
    else:
        await message.answer("❌ Xatolik! Qayta urinib ko'ring.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
