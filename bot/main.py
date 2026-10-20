import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import settings
from handlers import all_rts
from services.reminder_worker import reminder_worker


async def start_reminders(bot: Bot) -> tuple[asyncio.Event, asyncio.Task | None]:
    stop = asyncio.Event()
    task = asyncio.create_task(reminder_worker(bot, stop)) if settings.REMINDERS_ENABLED else None
    return stop, task


async def stop_reminders(stop: asyncio.Event, task: asyncio.Task | None) -> None:
    stop.set()
    if task:
        try:
            await asyncio.wait_for(task, timeout=30)
        except asyncio.TimeoutError:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


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
    reminder_stop, reminder_task = await start_reminders(bot)
    try:
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        await stop_reminders(reminder_stop, reminder_task)
        await bot.session.close()


async def on_webhook_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.WEBHOOK_SECRET,
        allowed_updates=["message"],
    )
    logging.info("Telegram webhook configured")


def create_webhook_app() -> web.Application:
    bot = create_bot()
    dispatcher = create_dispatcher()
    app = web.Application()
    reminder_state = None

    async def reminder_lifecycle(_app):
        nonlocal reminder_state
        stop, task = await start_reminders(bot)
        reminder_state = (stop, task)
        yield
        await stop_reminders(stop, task)

    app.cleanup_ctx.append(reminder_lifecycle)

    async def stop_before_session_closes(_app):
        if reminder_state:
            await stop_reminders(*reminder_state)

    # The request handler closes the bot session in on_shutdown, before cleanup.
    app.on_shutdown.append(stop_before_session_closes)

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    ).register(app, path=settings.WEBHOOK_PATH)

    dispatcher.startup.register(on_webhook_startup)
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
