from aiogram import Router, Bot
from aiogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, WebAppInfo,
)
from aiogram.filters import Command
from html import escape
from services.reminder_worker import app_url

from config import settings
from services.backend_client import backend
from services.tg_utils import get_avatar_url

rt = Router()


@rt.message(Command("start"))
async def start(message: Message, bot: Bot):
    user = message.from_user

    avatar_url = await get_avatar_url(bot, user.id)

    result = await backend.get_or_create_user(
        tg_id=str(user.id),
        name=user.first_name,
        second_name=user.last_name,
        username=user.username,
        avatar_url=avatar_url,
    )

    is_new = result.get("created", False)
    greeting = "Добро пожаловать" if is_new else "С возвращением"

    await message.answer(
        f"{greeting}, {escape(user.first_name)}! 👋\nОткрой приложение по кнопке ниже.\n"
        "В разделе «Мой план» можно составить расписание и включить напоминания.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Открыть приложение",
                web_app=WebAppInfo(url=settings.WEB_APP_URL),
            )],
            [InlineKeyboardButton(text="Мой план и напоминания", web_app=WebAppInfo(url=app_url("/planner")))],
        ]),
    )


@rt.message(Command("plan", "reminders"))
async def open_plan(message: Message):
    if message.chat.type != "private":
        return
    await message.answer(
        "Выбери дни занятий или поставь напоминание о конкретной теме. "
        "Расписание и переносы доступны в приложении.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Мой план и напоминания", web_app=WebAppInfo(url=app_url("/planner")))],
        ]),
    )
