from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
import os
import asyncio
import traceback

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()


@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        print("ERROR parsing JSON:", e)
        traceback.print_exc()
        return {"ok": False, "error": "bad json"}

    # log raw update for debugging
    print("Incoming update:", data)

    # Try to construct Update object safely
    try:
        update = types.Update(**data)
    except Exception as e:
        print("ERROR creating aiogram.Update:", e)
        traceback.print_exc()
        # Return 200 so Telegram won't keep retrying too fast,
        # but Telegram will still show this in getWebhookInfo.
        return {"ok": True, "note": "update parse failed"}

    # Process update in background so we quickly return 200 to Telegram
    try:
        asyncio.create_task(dp.feed_update(bot, update))
    except Exception as e:
        print("ERROR feeding update to dispatcher:", e)
        traceback.print_exc()
        return {"ok": False, "error": "dispatch failed"}

    return {"ok": True}
