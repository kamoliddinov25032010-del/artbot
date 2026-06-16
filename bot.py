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
user_counts = {}
premium_users = set()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎨 Salom! Men san'at yaratuvchi botman!\n\n"
        "🆓 Bepul: kuniga 3 ta rasm\n"
        "⭐ Premium: 50 Stars = cheksiz rasm\n\n"
        "Rasm olish uchun tasvirni yozing!\n"
        "Masalan: sunset mountains"
    )

@dp.message(Command("premium"))
async def premium(message: types.Message):
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="⭐ Premium obuna",
        description="Cheksiz rasm yaratish imkoniyati!",
        payload="premium_subscription",
        currency="XTR",
        prices=[LabeledPrice(label="Premium", amount=PREMIUM_PRICE)]
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: types.Message):
    premium_users.add(message.from_user.id)
    await message.answer("🎉 Premium faollashdi! Endi cheksiz rasm yaratishingiz mumkin!")

@dp.message()
a
