from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
import os
import asyncio

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()


@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update(**data)

    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "ok", "message": "HR bot working"}
