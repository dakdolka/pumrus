import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import settings
from handlers import all_rts


def create_bot() -> Bot:
    session = AiohttpSession(proxy=settings.TG_PROXY)
    return Bot(
        token=settings.TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    for router in all_rts:
        dispatcher.include_router(router)
    return dispatcher


async def run_polling() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


async def on_webhook_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.WEBHOOK_SECRET,
        allowed_updates=["message"],
    )
    logging.info("Telegram webhook configured")


async def on_webhook_shutdown(bot: Bot) -> None:
    # Keep the webhook registered during restarts. Telegram will retry pending
    # updates when the service becomes available again.
    await bot.session.close()


def create_webhook_app() -> web.Application:
    bot = create_bot()
    dispatcher = create_dispatcher()
    app = web.Application()

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    ).register(app, path=settings.WEBHOOK_PATH)

    dispatcher.startup.register(on_webhook_startup)
    dispatcher.shutdown.register(on_webhook_shutdown)
    setup_application(app, dispatcher, bot=bot)

    async def healthcheck(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "mode": "webhook"})

    app.router.add_get("/healthz", healthcheck)
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if settings.BOT_MODE == "webhook":
        web.run_app(
            create_webhook_app(),
            host=settings.WEBHOOK_HOST,
            port=settings.WEBHOOK_PORT,
        )
        return

    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
