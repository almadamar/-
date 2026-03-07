import os, logging, glob, importlib, asyncio, yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- [الإعدادات] ---
OWNER_ID = 162459553 
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'
DB_FILE = "users.txt"

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

active_users = set()
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if line.strip(): active_users.add(int(line.strip()))

def save_user(uid):
    if uid not in active_users:
        active_users.add(uid)
        with open(DB_FILE, "a") as f: f.write(f"{uid}\n")

load_db()

async def is_subscribed(bot, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)
    url = update.message.text
    if not url.startswith("http"): return
    
    if not await is_subscribed(context.bot, uid):
        btn = [[InlineKeyboardButton("📢 انضم للقناة", url=CHANNEL_LINK)]]
        await update.message.reply_text("⚠️ اشترك أولاً ثم أرسل الرابط.", reply_markup=InlineKeyboardMarkup(btn))
        return

    msg = await update.message.reply_text("⏳ جاري تحميل الفيديو (720p)...")
    
    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best', 
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'nocheckcertificate': True,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        },
        'max_filesize': 48 * 1024 * 1024 
    }

    try:
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        with open(file_path, 'rb') as f:
            await update.message.reply_video(video=f, caption="✅ تم التحميل بجودة 720p")
        
        if os.path.exists(file_path): os.remove(file_path)
        await msg.delete()
    except Exception as e:
        logging.error(f"Error: {e}")
        await msg.edit_text("❌ فشل التحميل. يوتيوب/إنستا قد يكونوا حظروا السيرفر حالياً.")

def load_plugins(app):
    for f in glob.glob("plugin_*.py"):
        try:
            m = importlib.import_module(f[:-3])
            if hasattr(m, "setup"): m.setup(app)
        except Exception as e: logging.error(f"Plugin Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    load_plugins(app)
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("أرسل الرابط للتحميل مباشرة.")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🚀 البوت بدأ العمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
