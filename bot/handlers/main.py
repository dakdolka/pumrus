from aiogram import Bot, Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
# from buttons import kb_for_songs, kb_main, kb_confirm_for_file, kb_confirm_for_link, kb_confirm_for_name, create_kb_for_change, Last_kb, kb_exit_to_main
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from config import settings
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional
from aiogram.filters.callback_data import CallbackData
from collections import defaultdict



rt = Router()

@rt.message(Command("start"))
async def start(message: Message):
    await message.answer("Открой приложение по кнопке ниже!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть приложение", url=f"{settings.WEB_APP_URL}")],
    ]))
    