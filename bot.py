import asyncio
import sqlite3
import time
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus

# ========== CONFIG ==========
API_ID = 743554
API_HASH = "b440caaf2c2763fdc72bbb8350dfd6b8"
BOT_TOKEN = "6803200402:AAFtNX2L6T0KfFbjLqq7I9Nr1ghbvqtBTA8"

ADMINS = [1940757150]
CHANNEL_ID = "@Seriallar_kanaliuz"

app = Client(
    "Asilmediatv_bot",
    api_id=743554,
    api_hash="b440caaf2c2763fdc72bbb8350dfd6b8",
    bot_token="6803200402:AAFtNX2L6T0KfFbjLqq7I9Nr1ghbvqtBTA8"
)

# ========== DATABASE ==========
db = sqlite3.connect("kino.db", check_same_thread=False)
sql = db.cursor()

sql.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
sql.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    title TEXT,
    file_id TEXT
)
""")
sql.execute("""
CREATE TABLE IF NOT EXISTS premium (
    user_id INTEGER PRIMARY KEY,
    until INTEGER
)
""")
db.commit()

# ========== HELPERS ==========
def is_premium(uid):
    row = sql.execute(
        "SELECT until FROM premium WHERE user_id=?",
        (uid,)
    ).fetchone()
    return row and row[0] > int(time.time())

async def subscribed(uid):
    try:
        member = await app.get_chat_member(CHANNEL_ID, uid)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False

# ========== START ==========
@app.on_message(filters.command("start"))
async def start(_, m):
    uid = m.from_user.id
    sql.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    db.commit()
    await m.reply("🎬 Kino botga xush kelibsiz!\nKino nomi yoki kodini yuboring.")

# ========== ADD MOVIE ==========
@app.on_message(filters.command("addmovie") & filters.user(ADMINS))
async def add_movie(_, m):
    try:
        _, code, title = m.text.split(" ", 2)
        if not m.reply_to_message or not m.reply_to_message.video:
            await m.reply("❌ Videoga reply qilib yozing")
            return

        file_id = m.reply_to_message.video.file_id
        sql.execute(
            "INSERT OR REPLACE INTO movies VALUES (?,?,?)",
            (code, title, file_id)
        )
        db.commit()
        await m.reply(f"✅ Kino saqlandi\n🎟 Kod: `{code}`")
    except:
        await m.reply("❌ Format: /addmovie KOD NOMI (videoga reply)")

# ========== DELETE ==========
@app.on_message(filters.command("delmovie") & filters.user(ADMINS))
async def del_movie(_, m):
    if len(m.command) < 2:
        await m.reply("❌ Kino kodi yozing")
        return
    sql.execute("DELETE FROM movies WHERE code=?", (m.command[1],))
    db.commit()
    await m.reply("🗑 O‘chirildi")

# ========== STATS ==========
@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats(_, m):
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    k = sql.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    p = sql.execute("SELECT COUNT(*) FROM premium").fetchone()[0]
    await m.reply(f"📊 Statistika\n👤 {u}\n🎬 {k}\n💎 {p}")

# ========== PREMIUM ==========
@app.on_message(filters.command("premium") & filters.user(ADMINS))
async def premium(_, m):
    try:
        uid = int(m.command[1])
        days = int(m.command[2])
        until = int(time.time()) + days * 86400
        sql.execute(
            "INSERT OR REPLACE INTO premium VALUES (?,?)",
            (uid, until)
        )
        db.commit()
        await m.reply("💎 Premium berildi")
    except:
        await m.reply("❌ /premium USER_ID KUN")

# ========== SEARCH ==========
@app.on_message(filters.text & ~filters.command)
async def search(_, m):
    uid = m.from_user.id

    if not is_premium(uid):
        if not await subscribed(uid):
            await m.reply(f"❌ Avval kanalga obuna bo‘ling:\n{CHANNEL_ID}")
            return

    q = m.text.lower()
    row = sql.execute(
        "SELECT file_id, title FROM movies WHERE code=? OR title LIKE ?",
        (q, f"%{q}%")
    ).fetchone()

    if not row:
        await m.reply("❌ Kino topilmadi")
        return

    await app.send_video(
        m.chat.id,
        row[0],
        caption=f"🎬 {row[1]}",
        protect_content=True
    )

# ========== RUN ==========
async def main():
    await app.start()
    print("Bot ishga tushdi")
    await asyncio.Event().wait()

asyncio.run(main())
