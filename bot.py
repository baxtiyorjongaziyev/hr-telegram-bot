import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================== CONFIG ==================

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/api/webhook")

# 👉 BU YERGA INTRO DOIRA VIDEO file_id QO‘YASAN
INTRO_VIDEO_FILE_ID = "PASTE_VIDEO_NOTE_FILE_ID_HERE"

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")

logging.basicConfig(level=logging.INFO)

# ================== INIT ==================

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

# ================== STATES ==================

class Form(StatesGroup):
    role = State()
    name = State()

# ================== KEYBOARDS ==================

role_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Sotuv menejeri", callback_data="role_sales")],
    [InlineKeyboardButton(text="SMM mutaxassisi", callback_data="role_smm")],
    [InlineKeyboardButton(text="Kopirayter", callback_data="role_copy")],
    [InlineKeyboardButton(text="Volontyor", callback_data="role_vol")]
])

# ================== HANDLERS ==================

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()

    # 1️⃣ INTRO VIDEO
    await message.answer_video_note(
        video_note=INTRO_VIDEO_FILE_ID
    )

    # 2️⃣ LAVOZIM TANLASH
    await message.answer(
        "Kompaniyamizda qaysi lavozimda ishlamoqchisiz?",
        reply_markup=role_kb
    )

    await state.set_state(Form.role)

@dp.callback_query(lambda c: c.data.startswith("role_"), state=Form.role)
async def role_chosen(cb: types.CallbackQuery, state: FSMContext):
    role_map = {
        "role_sales": "Sotuv menejeri",
        "role_smm": "SMM mutaxassisi",
        "role_copy": "Kopirayter",
        "role_vol": "Volontyor"
    }

    role = role_map.get(cb.data)
    await state.update_data(role=role)

    await cb.message.answer("Ismingizni yozing. Masalan: Ali Valiyev")
    await state.set_state(Form.name)
    await cb.answer()

@dp.message(state=Form.name)
async def name_received(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    data = await state.get_data()

    await message.answer(
        f"✅ Qabul qilindi:\n\n"
        f"👤 Ism: <b>{data['name']}</b>\n"
        f"💼 Lavozim: <b>{data['role']}</b>\n\n"
        f"Keyingi bosqichni davom ettiramiz…"
    )

    await state.clear()

# ================== FILE_ID OLISH (ADMIN) ==================

@dp.message(Command("fileid"))
async def get_file_id(message: types.Message):
    if message.video_note:
        await message.answer(
            f"🎥 Video_note file_id:\n<code>{message.video_note.file_id}</code>"
        )
    elif message.video:
        await message.answer(
            f"🎬 Video file_id:\n<code>{message.video.file_id}</code>"
        )
    else:
        await message.answer("❌ Avval video yuboring, keyin /fileid yozing.")

# ================== WEBHOOK ==================

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    update = types.Update(**payload)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# ================== HEALTH ==================

@app.get("/")
async def health():
    return {"status": "ok", "bot": "HR Telegram Bot"}
