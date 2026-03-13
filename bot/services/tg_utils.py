from aiogram import Bot


async def get_avatar_url(bot: Bot, user_id: int) -> str | None:
    """Возвращает file_path первой фотографии профиля или None."""
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if not photos.photos:
            return None
        file_id = photos.photos[0][-1].file_id  # наибольшее разрешение
        file = await bot.get_file(file_id)
        return f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    except Exception:
        return None
