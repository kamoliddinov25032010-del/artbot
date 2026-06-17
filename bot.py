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
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated
    except:
        return text

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
    await message.answer(
        "🎨 Salom! Men kuchli san'at botman!\n\n"
        "🖼 Rasm yaratish — o'zbek yoki inglizcha yozing\n"
        "🎭 Uslub tanlash — /style\n"
        "⭐ Premium — /premium\n\n"
        "Boshlang! 🚀"
    )

@dp.message(Command("style"))
async def style_cmd(message: types.Message):
    await message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())

@dp.callback_query(lambda c: c.data.startswith("style_"))
async def style_selected(callback: CallbackQuery):
    style = callback.data.replace("style_", "")
    user_styles[callback.from_user.id] = style
    await callback.answer(f"{STYLE_NAMES[style]} tanlandi!")
    await callback.message.answer(f"✅ {STYLE_NAMES[style]} uslubi tanlandi!\n\nEndi rasm yaratish uchun matn yozing!")

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
    is_owner = user_id == OWNER_ID
    if not is_owner and user_id not in premium_users and user_counts[user_id] >= FREE_LIMIT:
        await message.answer("⭐ Limit tugadi! Premium: /premium\n50 Stars = cheksiz rasm!")
        return
    await message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    success = await create_image(message, message.text, user_id)
    if success:
        if not is_owner and user_id not in premium_users:
            user_counts[user_id] += 1
            remaining = FREE_LIMIT - user_counts[user_id]
            if remaining > 0:
                await message.answer(f"💡 Bugun yana {remaining} ta bepul rasm qoldi!")
    else:
        await message.answer("❌ Xatolik! Qayta urinib ko'ring.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
