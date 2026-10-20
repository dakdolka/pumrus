"""Delivery stays in the bot so it uses the existing Telegram proxy/session."""
import asyncio
import logging
from html import escape
from urllib.parse import urlsplit, urlunsplit

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter,
    TelegramNetworkError, TelegramServerError,
)
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import settings
from services.backend_client import backend

logger = logging.getLogger(__name__)


def app_url(path: str) -> str:
    base = urlsplit(settings.WEB_APP_URL)
    target = urlsplit(path)
    # Paths originate from the backend's validated catalog, never from messages.
    if target.scheme or target.netloc or not path.startswith("/") or path.startswith("//"):
        raise ValueError("Invalid reminder target")
    return urlunsplit((base.scheme, base.netloc, target.path, target.query, ""))


async def deliver(bot: Bot, item: dict) -> dict:
    try:
        await bot.send_message(
            chat_id=int(item["telegramId"]),
            text=f"⏰ <b>Время для занятия</b>\n\n{escape(item['title'])}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Открыть материал", web_app=WebAppInfo(url=app_url(item["targetPath"])))],
                [InlineKeyboardButton(text="Мой план · перенести занятие", web_app=WebAppInfo(
                    url=app_url(f"/planner?reminder={item['id']}")))],
            ]),
            request_timeout=20,
        )
        return {"outcome": "sent"}
    except TelegramRetryAfter as error:
        return {"outcome": "retry", "retry_after": min(86400, max(1, int(error.retry_after)))}
    except TelegramForbiddenError:
        return {"outcome": "blocked"}
    except (TelegramBadRequest, ValueError):
        return {"outcome": "failed"}
    except (TelegramNetworkError, TelegramServerError, asyncio.TimeoutError):
        return {"outcome": "retry"}


async def reminder_worker(bot: Bot, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            batch = await backend.reminder_request("/claim")
            for item in batch["items"]:
                if stop.is_set():
                    break
                result = await deliver(bot, item)
                # If the receipt is lost, the durable lease permits recovery.
                # Telegram sendMessage has no idempotency key: delivery is at least once.
                await backend.reminder_request(f"/{item['id']}/receipt", {"token": item["token"], **result})
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            # Do not log request URLs: they can contain Telegram credentials.
            logger.warning("Reminder delivery iteration failed (%s)", type(error).__name__)
        try:
            await asyncio.wait_for(stop.wait(), timeout=15)
        except asyncio.TimeoutError:
            pass
