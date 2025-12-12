# bot.py
import os
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import State, StatesGroup

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "0")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/api/webhook")
DB_PATH = os.getenv("DB_PATH", "hrbot.db")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set in .env")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

app = FastAPI()

# --- States ---
class Form(StatesGroup):
    lang = State()
    name = State()
    phone = State()
    role = State()
    experience = State()
    prev_place = State()
    video = State()
    voice = State()
    birth = State()
    city = State()
    russian = State()
    marriage = State()
    salary = State()

# --- Keyboards ---
lang_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="O'zbekcha", callback_data="lang_uz")],
    [InlineKeyboardButton(text="Русский", callback_data="lang_ru")]
])

role_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
role_kb.add(KeyboardButton("Tur agent"), KeyboardButton("Sotuv manageri"), KeyboardButton("Boshqa"))

yn_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
yn_kb.add(KeyboardButton("Ha"), KeyboardButton("Yo'q"))

start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(KeyboardButton("/start"))

# --- DB ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            lang TEXT,
            name TEXT,
            phone TEXT,
            role TEXT,
            experience TEXT,
            prev_place TEXT,
            video_file_id TEXT,
            voice_file_id TEXT,
            birth TEXT,
            city TEXT,
            russian TEXT,
            marriage TEXT,
            salary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.commit()

asyncio.get_event_loop().run_until_complete(init_db())

async def save_applicant(data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO applicants (telegram_id, lang, name, phone, role, experience, prev_place, video_file_id, voice_file_id, birth, city, russian, marriage, salary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("telegram_id"),
            data.get("lang"),
            data.get("name"),
            data.get("phone"),
            data.get("role"),
            data.get("experience"),
            data.get("prev_place"),
            data.get("video_file_id"),
            data.get("voice_file_id"),
            data.get("birth"),
            data.get("city"),
            data.get("russian"),
            data.get("marriage"),
            data.get("salary")
        ))
        await db.commit()

async def notify_admin(data: dict):
    if not ADMIN_CHAT_ID or ADMIN_CHAT_ID in ("0", "None"):
        return
    try:
        text = (
            f"Yangi nomzod\n"
            f"Ism: {data.get('name')}\n"
            f"Tel: {data.get('phone')}\n"
            f"Lavozim: {data.get('role')}\n"
            f"Taj: {data.get('experience')}\n"
            f"Sh: {data.get('city')}\n"
            f"Yosh: {data.get('birth')}\n"
            f"Oylik kut: {data.get('salary')}\n"
            f"ID: {data.get('telegram_id')}"
        )
        await bot.send_message(int(ADMIN_CHAT_ID), text)
        if data.get("video_file_id"):
            try:
                await bot.send_video(int(ADMIN_CHAT_ID), data.get("video_file_id"))
            except Exception:
                pass
        if data.get("voice_file_id"):
            try:
                await bot.send_voice(int(ADMIN_CHAT_ID), data.get("voice_file_id"))
            except Exception:
                pass
    except Exception as e:
        logging.exception("notify_admin error: %s", e)

# --- Handlers (aiogram) ---

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Iltimos, tilni tanlang / Пожалуйста, выберите язык:", reply_markup=ReplyKeyboardRemove())
    await message.answer("Tilni tanlang:", reply_markup=lang_kb)
    await state.set_state(Form.lang)

@dp.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def lang_chosen(cb: types.CallbackQuery, state: FSMContext):
    lang = "uz" if cb.data == "lang_uz" else "ru"
    await state.update_data(lang=lang)
    await cb.message.answer("Ismingizni yozing. Namuna: Hojakbar Ravshanov" if lang=="uz" else "Напишите имя. Пример: Hojakbar Ravshanov")
    await state.set_state(Form.name)
    await cb.answer()

@dp.message(lambda message: True, state=Form.name)
async def name_received(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Telefon raqamingizni yuboring.")
    await state.set_state(Form.phone)

@dp.message(lambda message: True, state=Form.phone)
async def phone_received(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("👍 Sizga qaysi lavozimda ishlash qulay?", reply_markup=role_kb)
    await state.set_state(Form.role)

@dp.message(lambda message: True, state=Form.role)
async def role_received(message: types.Message, state: FSMContext):
    await state.update_data(role=message.text.strip())
    await message.answer("Bu sohаda nechi yillik tajribangiz bor? (raqam yoki matn)")
    await state.set_state(Form.experience)

@dp.message(lambda message: True, state=Form.experience)
async def exp_received(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text.strip())
    await message.answer("Avval qayerlarda ishlagansiz?")
    await state.set_state(Form.prev_place)

@dp.message(lambda message: True, state=Form.prev_place)
async def prev_place_received(message: types.Message, state: FSMContext):
    await state.update_data(prev_place=message.text.strip())
    await message.answer("O'zingiz haqida 1 minutlik video xabar yuboring (doira shaklida selfi-video). Maks 60 soniya.")
    await state.set_state(Form.video)

@dp.message(state=Form.video, content_types=types.ContentType.VIDEO_NOTE | types.ContentType.VIDEO)
async def video_handler(message: types.Message, state: FSMContext):
    if message.video_note:
        dur = message.video_note.duration or 0
        if dur > 60:
            await message.answer("❌ Video juda uzun. Iltimos, 60s dan qisqaroq doira video yuboring.")
            return
        await state.update_data(video_file_id=message.video_note.file_id)
    elif message.video:
        dur = message.video.duration or 0
        if dur > 60:
            await message.answer("❌ Video juda uzun. Maks 60s.")
            return
        await state.update_data(video_file_id=message.video.file_id)
    else:
        await message.answer("❌ Iltimos video yuboring.")
        return
    await message.answer("Video qabul qilindi. Endi ovozli xabar yuboring (o'zingiz haqida).")
    await state.set_state(Form.voice)

@dp.message(state=Form.voice, content_types=types.ContentType.VOICE)
async def voice_handler(message: types.Message, state: FSMContext):
    if not message.voice:
        await message.answer("❌ Iltimos ovozli xabar yuboring.")
        return
    await state.update_data(voice_file_id=message.voice.file_id)
    await message.answer("Yoshingizni yozing. Namuna: 01.01.2000")
    await state.set_state(Form.birth)

@dp.message(lambda message: True, state=Form.birth)
async def birth_handler(message: types.Message, state: FSMContext):
    await state.update_data(birth=message.text.strip())
    await message.answer("Doimiy yashash manzilingizni yozing.")
    await state.set_state(Form.city)

@dp.message(lambda message: True, state=Form.city)
async def city_handler(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("Rus tilini bilasizmi?", reply_markup=yn_kb)
    await state.set_state(Form.russian)

@dp.message(lambda message: True, state=Form.russian)
async def russian_handler(message: types.Message, state: FSMContext):
    await state.update_data(russian=message.text.strip())
    await message.answer("Yaqin 1 yil ichida uylanmasizmi yoki erga tegmayasmi?", reply_markup=yn_kb)
    await state.set_state(Form.marriage)

@dp.message(lambda message: True, state=Form.marriage)
async def marriage_handler(message: types.Message, state: FSMContext):
    await state.update_data(marriage=message.text.strip())
    await message.answer("Qancha oylik taklif qilsak ishlagan bo'lar edingiz? Yozib qoldiring.")
    await state.set_state(Form.salary)

@dp.message(lambda message: True, state=Form.salary)
async def salary_handler(message: types.Message, state: FSMContext):
    await state.update_data(salary=message.text.strip())
    data = await state.get_data()
    payload = {
        "telegram_id": message.from_user.id,
        **data
    }
    await save_applicant(payload)
    await notify_admin(payload)
    await message.answer("✅ Rahmat! Ma'lumotlaringiz qabul qilindi. Tez orada sizga murojaat qilamiz.", reply_markup=start_kb)
    await state.clear()

# Fallback
@dp.message()
async def fallback(message: types.Message):
    await message.answer("Iltimos, /start bilan boshlang yoki kerakli shaklda javob bering.")

# --- Webhook endpoint for Vercel / any serverless ---
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    update = types.Update(**payload)
    # process update via dispatcher
    try:
        await dp.feed_update(update)  # aiogram v3-ish helper; works in many setups
    except AttributeError:
        # fallback: try process_update (some versions)
        try:
            await dp.process_update(update)
        except Exception as e:
            logging.exception("Dispatcher handling error: %s", e)
    except Exception as e:
        logging.exception("Dispatcher feed_update error: %s", e)
    return JSONResponse(content={"ok": True})

# health
@app.get("/")
async def root():
    return {"status": "ok"}

# For local testing with `uvicorn bot:app --reload`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
