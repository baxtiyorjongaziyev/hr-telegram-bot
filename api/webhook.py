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

    print("Incoming update:", data)

    try:
        update = types.Update(**data)
    except Exception as e:
        print("ERROR creating aiogram.Update:", e)
        traceback.print_exc()
        return {"ok": True, "note": "update parse failed"}

    try:
        asyncio.create_task(dp.feed_update(bot, update))
    except Exception as e:
        print("ERROR feeding update to dispatcher:", e)
        traceback.print_exc()
        return {"ok": False, "error": "dispatch failed"}

    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "ok", "message": "HR bot working"}
