import asyncio
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message

# ========= CONFIG =========
API_ID = id:743554,
API_HASH = "b440caaf2c2763fdc72bbb8350dfd6b8"
BOT_TOKEN = "6610724048:AAG2MxcmUeLZOhRvvXqhwv42p6eui4pShgw"

CHANNEL_ID = -1002007689198   # majburiy obuna
ADMINS = [1940757150]
# ==========================

app = Client(
    "Uzmovi_tarjima_bot",
    api_id=743554,
    api_hash="b440caaf2c2763fdc72bbb8350dfd6b8",
    bot_token="6610724048:AAG2MxcmUeLZOhRvvXqhwv42p6eui4pShgw"
)

# ========= DATABASE =========
db = sqlite3.connect("movies.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY,
    title TEXT,
    file_id TEXT
)
""")
db.commit()
# ============================

# ========= OBUNA TEKSHIRISH =========
async def subscribed(user_id: int) -> bool:
    try:
        m = await app.get_chat_member(CHANNEL_ID, -1002007689198)
        return m.status in ("member", "administrator", "owner")
    except:
        return False
# ===================================

# ========= START =========
@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    if not await subscribed(m.from_user.id):
        await m.reply(f"❌ Avval kanalga obuna bo‘ling:\n{-1002007689198}")
        return
    await m.reply("🎬 Kino bot ishga tushdi!\nKino kodini yuboring.")
# =========================

# ========= ADMIN: ADD =========
@app.on_message(filters.command("add") & filters.private)
async def add_movie(_, m: Message):
    if m.from_user.id not in ADMINS:
        return

    if not m.reply_to_message or not m.reply_to_message.video:
        await m.reply("❌ Videoga reply qilib yuboring:\n/add KOD NOMI")
        return

    try:
        _, code, title = m.text.split(" ", 2)
    except:
        await m.reply("❌ Format: /add KOD NOMI")
        return

    file_id = m.reply_to_message.video.file_id
    sql.execute(
        "INSERT OR REPLACE INTO movies VALUES (?,?,?)",
        (code.lower(), title, file_id)
    )
    db.commit()

    await m.reply(f"✅ Qo‘shildi:\n🎬 {title}\n🔑 Kod: {code}")
# ================================

# ========= SEARCH =========
@app.on_message(filters.text & filters.private)
async def search(_, m: Message):
    if not await subscribed(m.from_user.id):
        await m.reply(f"❌ Avval kanalga obuna bo‘ling:\n{-1002007689198}")
        return

    q = m.text.lower().strip()

    row = sql.execute(
        "SELECT title, file_id FROM movies WHERE code=? OR title LIKE ?",
        (q, f"%{q}%")
    ).fetchone()

    if not row:
        await m.reply("❌ Kino topilmadi")
        return

    await app.send_video(
        chat_id=m.chat.id,
        video=row[1],
        caption=f"🎬 {row[0]}",
        protect_content=True
    )
# ===========================

# ========= RUN =========
async def main():
    await app.start()
    print("Bot ishga tushdi")
    await asyncio.Event().wait()

asyncio.run(main())
