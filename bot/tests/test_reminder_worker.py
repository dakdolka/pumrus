import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import SendMessage

from config import settings
from services.reminder_worker import app_url, deliver, reminder_worker


class ReminderBotTests(unittest.IsolatedAsyncioTestCase):
    def item(self):
        return {"id": 3, "token": "test-token", "telegramId": "101", "title": "<b>Моя тема & практика</b>",
                "targetPath": "/practice/tasks/9?topic=10"}

    def test_deep_links_and_external_path_rejected(self):
        with patch.object(settings, "WEB_APP_URL", "https://example.com/?old=1"):
            self.assertEqual(app_url("/practice/tasks/9?topic=10"), "https://example.com/practice/tasks/9?topic=10")
            for path in ["https://evil.test", "//evil.test", "relative"]:
                with self.assertRaises(ValueError):
                    app_url(path)

    async def test_message_escapes_content_and_links_to_material(self):
        bot = AsyncMock()
        result = await deliver(bot, self.item())
        self.assertEqual(result, {"outcome": "sent"})
        kwargs = bot.send_message.call_args.kwargs
        self.assertIn("&lt;b&gt;Моя тема &amp; практика&lt;/b&gt;", kwargs["text"])
        self.assertTrue(kwargs["reply_markup"].inline_keyboard[0][0].web_app.url.endswith("/practice/tasks/9?topic=10"))
        self.assertTrue(kwargs["reply_markup"].inline_keyboard[1][0].web_app.url.endswith("/planner?reminder=3"))

    async def test_telegram_errors_are_reported_to_queue(self):
        method = SendMessage(chat_id=101, text="test")
        cases = [
            (TelegramRetryAfter(method=method, message="limited", retry_after=120), {"outcome": "retry", "retry_after": 120}),
            (TelegramForbiddenError(method=method, message="blocked"), {"outcome": "blocked"}),
            (TelegramNetworkError(method=method, message="offline"), {"outcome": "retry"}),
            (TelegramBadRequest(method=method, message="invalid chat"), {"outcome": "failed"}),
        ]
        for error, expected in cases:
            bot = AsyncMock()
            bot.send_message.side_effect = error
            self.assertEqual(await deliver(bot, self.item()), expected)

    async def test_worker_records_receipt_and_stops(self):
        stop = asyncio.Event()
        calls = []

        async def backend_request(path, payload=None):
            calls.append((path, payload))
            if path == "/claim":
                return {"items": [self.item()]}
            stop.set()
            return {"accepted": True}

        with patch("services.reminder_worker.backend.reminder_request", side_effect=backend_request):
            await asyncio.wait_for(reminder_worker(AsyncMock(), stop), timeout=3)
        self.assertEqual(calls[1], ("/3/receipt", {"token": "test-token", "outcome": "sent"}))


if __name__ == "__main__":
    unittest.main()
