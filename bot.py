import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "8695232414:AAHxNwJtmaMQV4mPypHgLhMwDu4j5Kk0FB4"
HF_TOKEN = "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"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FREE_LIMIT = 3
user_counts = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎨 Salom! Men san'at yaratuvchi botman!\n\n🆓 Bepul: kuniga 3 ta rasm\n\nRasm olish uchun tasvirni yozing!")

@dp.message()
async def generate_image(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_counts:
        user_counts[user_id] = 0
    if user_counts[user_id] >= FREE_LIMIT:
        await message.answer("⭐ Bepul limitingiz tugadi!")
        return
    await message.answer("🎨 Rasm yaratilmoqda... biroz kuting!")
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": message.text}
        )
        if response.status == 200:
            image_data = await response.read()
            await message.answer_photo(
                photo=types.BufferedInputFile(image_data, filename="art.png"),
                caption=f"🎨 '{message.text}'"
            )
            user_counts[user_id] += 1
        else:
            await message.answer("❌ Xatolik yuz berdi!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
