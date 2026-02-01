import sqlite3
import time
import asyncio
from pyrogram import Client, filters

# ================= CONFIG =================
API_ID = 743554  # Telegram API ID
API_HASH = "b440caaf2c2763fdc72bbb8350dfd6b8"
BOT_TOKEN = "6803200402:AAFtNX2L6T0KfFbjLqq7I9Nr1ghbvqtBTA8"

ADMINS = [1940757150]  # Adminlar ID si
CHANNEL_ID = "@Seriallar_kanaliuz"  # Majburiy obuna kanali

# ================= INIT BOT =================
app = Client(
    "kino_bot",
    api_id=743554,
    api_hash="b440caaf2c2763fdc72bbb8350dfd6b8",
    bot_token="6803200402:AAFtNX2L6T0KfFbjLqq7I9Nr1ghbvqtBTA8"
)

# ================= DATABASE =================
db = sqlite3.connect("kino.db")
sql = db.cursor()

# Users table
sql.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY
)""")

# Movies table
sql.execute("""CREATE TABLE IF NOT EXISTS movies(
    code TEXT PRIMARY KEY,
    title TEXT,
    file_id TEXT
)""")

# Premium table
sql.execute("""CREATE TABLE IF NOT EXISTS premium(
    user_id INTEGER PRIMARY KEY,
    until INTEGER
)""")
db.commit()

# ================= HELPERS =================
def is_premium(user_id):
    row = sql.execute("SELECT until FROM premium WHERE user_id=?", (user_id,)).fetchone()
    if row and row[0] > int(time.time()):
        return True
    return False

def subscribed(user_id):
    try:
        member = app.get_chat_member(CHANNEL_ID, user_id)
        return member.status != "left"
    except:
        return False

# Example limit: 3 movies per day for non-premium
def can_watch(user_id):
    # You can implement a more complex daily limit system here
    return True

# ================= HANDLERS =================
@app.on_message(filters.command("start"))
async def start_cmd(_, m):
    await m.reply("🎬 Kino bot ishga tushdi!\nObuna bo‘ling va kinolarni tomosha qiling ✅")

@app.on_message(filters.command("addmovie") & filters.user(ADMINS))
async def add_movie(_, m):
    parts = m.text.split(maxsplit=3)
    if len(parts) < 4:
        await m.reply("❌ Format: /addmovie CODE 'TITLE' FILE_ID")
        return
    code, title, file_id = parts[1], parts[2], parts[3]
    sql.execute("INSERT OR REPLACE INTO movies VALUES (?,?,?)", (code, title, file_id))
    db.commit()
    await m.reply(f"✅ Kino saqlandi\n🎟 Kod: `{code}`")

@app.on_message(filters.command("delmovie") & filters.user(ADMINS))
async def del_movie(_, m):
    parts = m.text.split()
    if len(parts) < 2:
        await m.reply("❌ Kino kodi kerak")
        return
    code = parts[1]
    sql.execute("DELETE FROM movies WHERE code=?", (code,))
    db.commit()
    await m.reply("🗑 Kino o‘chirildi")

@app.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats(_, m):
    u = sql.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    k = sql.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    p = sql.execute("SELECT COUNT(*) FROM premium").fetchone()[0]
    await m.reply(f"📊 Statistika\n👤 Foydalanuvchilar: {u}\n🎬 Kinolar: {k}\n💎 Premium: {p}")

@app.on_message(filters.command("send") & filters.user(ADMINS))
async def broadcast(_, m):
    parts = m.text.split(" ", 1)
    if len(parts) < 2:
        await m.reply("❌ Xabar matnini kiriting")
        return
    text = parts[1]
    for (uid,) in sql.execute("SELECT user_id FROM users"):
        try:
            await app.send_message(uid, text)
        except:
            pass
    await m.reply("📨 Xabar yuborildi")

@app.on_message(filters.command("premium") & filters.user(ADMINS))
async def premium(_, m):
    parts = m.text.split()
    if len(parts) < 3:
        await m.reply("❌ Format: /premium USER_ID KUN")
        return
    try:
        uid, days = int(parts[1]), int(parts[2])
    except:
        await m.reply("❌ USER_ID va KUN raqam bo‘lishi kerak")
        return
    until = int(time.time()) + days*86400
    sql.execute("INSERT OR REPLACE INTO premium VALUES (?,?)", (uid, until))
    db.commit()
    await m.reply("💎 Premium berildi")

@app.on_message(filters.text & ~filters.command)
async def search(_, m):
    uid = m.from_user.id
    sql.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (uid,))
    db.commit()

    if not subscribed(uid):
        await m.reply("❌ Kanalga obuna bo‘ling")
        return

    if not is_premium(uid) and not can_watch(uid):
        await m.reply("❌ Limit tugadi. Premium oling.")
        return

    q = m.text.lower()
    r = sql.execute(
        "SELECT file_id,title FROM movies WHERE title LIKE ? OR code=?",
        (f"%{q}%", q)
    ).fetchone()
    if not r:
        await m.reply("❌ Kino topilmadi")
        return

    await app.send_video(
        m.chat.id,
        r[0],
        caption=f"🎬 {r[1]}",
        protect_content=True
    )

# ================= RUN =================
async def main():
    await app.start()
    print("Bot ishga tushdi")
    await asyncio.Event().wait()  # bot 24/7 ishlashi uchun

if __name__ == "__main__":
    asyncio.run(main())
