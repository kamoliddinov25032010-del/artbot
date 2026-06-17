import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
PREMIUM_PRICE = 50
OWNER_ID = 7695822564
user_counts = {}
premium_users = set()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎨 Salom! Men san'at yaratuvchi botman!\n\n🆓 Bepul: kuniga 3 ta rasm\n⭐ Premium: 50 Stars = cheksiz rasm\n\nRasm olish uchun tasvirni yozing!")

@dp.message(Command("premium"))
async def premium(message: types.Message):
    await bot.send_invoice(chat_id=message.chat.id, title="⭐ Premium obuna", description="Cheksiz rasm yaratish!", payload="premium", currency="XTR", prices=[LabeledPrice(label="Premium", amount=PREMIUM_PRICE)])

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(lambda m: m.successful_payment is not None)
async def payment_done(message: types.Message):
    premium_users.add(message.from_user.id)
    await message.answer("🎉 Premium faollashdi!")

@dp.message()
async def generate_image(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_counts:
        user_counts[user_id] = 0
    is_owner = user_id == OWNER_ID
    if not is_owner and user_id not in premium_users and user_counts[user_id] >= FREE_LIMIT:
        await message.answer("⭐ Limit tugadi! Premium: /premium")
        return
    await message.answer("🎨 Rasm yaratilmoqda...")
    prompt = message.text.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&nologo=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                await message.answer_photo(photo=types.BufferedInputFile(image_data, filename="art.png"), caption=f"🎨 {message.text}")
                if not is_owner and user_id not in premium_users:
                    user_counts[user_id] += 1
            else:
                await message.answer("❌ Xatolik!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
