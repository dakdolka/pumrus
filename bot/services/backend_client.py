import aiohttp
from config import settings


class BackendClient:
    def __init__(self):
        self.base_url = settings.API_URL

    async def get_or_create_user(
        self,
        tg_id: str,
        name: str,
        second_name: str | None = None,
        username: str | None = None,
        avatar_url: str | None = None,
    ) -> dict:
        payload = {
            "tg_id": tg_id,
            "name": name,
            "second_name": second_name,
            "username": username,
            "avatar_url": avatar_url,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/users/get-or-create",
                json=payload,
            ) as response:
                response.raise_for_status()
                return await response.json()


backend = BackendClient()
