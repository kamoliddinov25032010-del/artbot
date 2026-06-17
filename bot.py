import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎨 Salom! Men kuchli san'at botman!\n\n"
        "🖼 Rasm yaratish — matn yozing\n"
        "✏️ Rasm tahrirlash — rasm + matn yuboring\n"
        "🎭 Uslub tanlash — /style\n"
        "⭐ Premium — /premium\n\n"
        "Boshlang!"
    )

@dp.message(Command("style"))
async def style_cmd(message: types.Message):
    await message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())

@dp.callback_query(lambda c: c.data.startswith("style_"))
async def style_selected(callback: CallbackQuery):
    style = callback.data.replace("style_", "")
    await callback.answer(f"{STYLE_NAMES[style]} tanlandi!")
    await callback.message.answer(f"✅ {STYLE_NAMES[style]} uslubi tanlandi!\n\nEndi rasm yaratish uchun matn yozing!")

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
    await message.answer("🔍 Rasm tahlil qilinmoqda...")
    caption = message.caption or ""
    if caption:
        await message.answer(f"✏️ Rasm tahrirlash hozircha ishlanmoqda. Ko'p kuting!")
    else:
        await message.answer(
            "🖼 Chiroyli rasm!\n\n"
            "✏️ Rasmni tahrirlash uchun — rasm bilan birga matn yuboring!\n"
            "Masalan: 'ko'k rangga o'zgartir' yoki 'qor qo'sh'"
        )

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
    prompt = urllib.parse.quote(message.text)
    style = STYLES["realistic"]
    full_prompt = urllib.parse.quote(f"{message.text}, {style}")
    url = f"https://image.pollinations.ai/prompt/{full_prompt}?width=512&height=512&nologo=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                image_data = await response.read()
                await message.answer_photo(
                    photo=types.BufferedInputFile(image_data, filename="art.png"),
                    caption=f"🎨 {message.text}\n\n🎭 Uslub o'zgartirish: /style",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Qayta yaratish", callback_data=f"regen_{message.text[:50]}")],
                        [InlineKeyboardButton(text="🎭 Uslub o'zgartirish", callback_data="change_style")]
                    ])
                )
                if not is_owner and user_id not in premium_users:
                    user_counts[user_id] += 1
                    remaining = FREE_LIMIT - user_counts[user_id]
                    if remaining > 0:
                        await message.answer(f"💡 Bugun yana {remaining} ta bepul rasm qoldi!")
            else:
                await message.answer("❌ Xatolik! Qayta urinib ko'ring.")

@dp.callback_query(lambda c: c.data == "change_style")
async def change_style(callback: CallbackQuery):
    await callback.message.answer("🎨 Uslub tanlang:", reply_markup=style_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("regen_"))
async def regenerate(callback: CallbackQuery):
    text = callback.data.replace("regen_", "")
    await callback.message.answer(f"🔄 Qayta yaratilmoqda: {text}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
