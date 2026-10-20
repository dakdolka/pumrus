import os

import aiohttp
from config import settings


class BackendClient:
    def __init__(self):
        self.base_url = settings.API_URL
        self.internal_token = os.getenv("BACKEND_INTERNAL_TOKEN", "")

    async def reminder_request(self, path: str, payload: dict | None = None) -> dict:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(
                f"{self.base_url}/v2/internal/reminders{path}",
                json=payload or {},
                headers={"X-Internal-Key": self.internal_token},
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_or_create_user(
        self,
        tg_id: str,
        name: str,
        second_name: str | None = None,
        username: str | None = None,
        avatar_url: str | None = None,
    ) -> dict:
        payload = {
            "telegram_id": tg_id,
            "first_name": name,
            "last_name": second_name or "",
            "username": username,
            "avatar_url": avatar_url,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v2/internal/telegram-users",
                json=payload,
                headers={"X-Internal-Key": self.internal_token},
            ) as response:
                response.raise_for_status()
                return await response.json()


backend = BackendClient()
