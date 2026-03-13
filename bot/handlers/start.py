from aiogram import Router, Bot
from aiogram.types import (
    Message, InlineKeyboardMarkup,
    InlineKeyboardButton, WebAppInfo,
)
from aiogram.filters import Command

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
        f"{greeting}, {user.first_name}! 👋\nОткрой приложение по кнопке ниже.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Открыть приложение",
                web_app=WebAppInfo(url=settings.WEB_APP_URL),
            )],
        ]),
    )
