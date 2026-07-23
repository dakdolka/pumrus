import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from config import settings
from handlers import all_rts


async def main():
    # AiohttpSession с SOCKS5-прокси
    session = AiohttpSession(
        proxy=settings.TG_PROXY
    )

    bot = Bot(
        token=settings.TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher()

    for router in all_rts:
        dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    print("Bot started")
    asyncio.run(main())
