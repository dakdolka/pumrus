from aiogram import Bot, Dispatcher, Router     
from config import settings
import asyncio
from aiogram.types import Message
from aiogram.filters.command import Command
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo



bot = Bot(settings.TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text="Открыть WebApp",
        web_app=WebAppInfo(url=settings.WEB_APP_URL)
    )]])
    
    await message.answer("Нажми кнопку, чтобы открыть WebApp:", reply_markup=kb)
    
async def main():
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())

