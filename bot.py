import os
import logging
import asyncio
import random
import importlib
import glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# --- [نظام قاعدة البيانات البسيطة] ---
DB_FILE = "users.txt"
active_users = set()

def load_db():
    """تحميل المستخدمين من الملف عند بدء التشغيل"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if line.strip(): active_users.add(int(line.strip()))

def save_user(uid):
    """حفظ مستخدم جديد في الملف لضمان عدم ضياع الإحصائيات"""
    if uid not in active_users:
        active_users.add(uid)
        with open(DB_FILE, "a") as f:
            f.write(f"{uid}\n")

load_db() 
OWNER_ID = 162459553 

# ---------------- [الإعدادات] ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def download_video(query, context, url, mode):
    msg = await query.edit_message_text("⏳ جاري التحميل جودة 720p...")
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        path = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]) or yt_dlp.YoutubeDL(ydl_opts).prepare_filename(yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)))
        final_path = path if mode == 'vid' else os.path.splitext(path)[0] + '.mp3'
        
        with open(final_path, 'rb') as f:
            caption = "✅ تم بواسطة @Down2024_bot"
            if mode == 'vid': await query.message.reply_video(f, caption=caption)
            else: await query.message.reply_audio(f, caption=caption)
        
        if os.path.exists(final_path): os.remove(final_path)
        await msg.delete()
    except: await msg.edit_text("❌ فشل التحميل.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid) 
    
    if await is_subscribed(context.bot, uid):
        msg = "🚀 أرسل الرابط للتحميل المباشر."
        if uid == OWNER_ID:
            msg += "\n\n🛠 **أوامر المطور:**\n/stats - الإحصائيات\n/broadcast - الإذاعة"
        await update.message.reply_text(msg)
    else:
        btn = [[InlineKeyboardButton("📢 اشترك هنا", url=CHANNEL_LINK)], [InlineKeyboardButton("✅ اشتركت", callback_data="check")]]
        await update.message.reply_text("⚠️ اشترك أولاً:", reply_markup=InlineKeyboardMarkup(btn))

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.startswith("http"): return
    if not await is_subscribed(context.bot, update.effective_user.id): return
    lid = str(random.randint(100, 999))
    context.user_data[lid] = update.message.text
    keys = [[InlineKeyboardButton("🎬 فيديو", callback_data=f"vid|{lid}"), InlineKeyboardButton("🎵 صوت", callback_data=f"aud|{lid}")]]
    await update.message.reply_text("اختر الصيغة:", reply_markup=InlineKeyboardMarkup(keys))

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التحقق!")
    elif "|" in query.data:
        mode, lid = query.data.split("|")
        url = context.user_data.get(lid)
        if url: await download_video(query, context, url, mode)

def load_plugins(app):
    for f in glob.glob("plugin_*.py"):
        module_name = f[:-3]
        try:
            m = importlib.import_module(module_name)
            importlib.reload(m)
            if hasattr(m, "setup"): m.setup(app)
            print(f"✅ تم ربط: {module_name}")
        except Exception as e: print(f"❌ خطأ: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(cb))
    load_plugins(app)
    print("--- البوت الأساسي يعمل وجاهز ---")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
