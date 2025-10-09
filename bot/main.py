from aiogram import Bot, Dispatcher, Router     
from config import settings
import asyncio
from aiogram.types import Message
from aiogram.filters.command import Command
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from handlers import all_rts

bot = Bot(settings.TOKEN)
dp = Dispatcher()

for elem in all_rts:
    dp.include_router(elem)
    



async def main():
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    print('start')
    asyncio.run(main())

