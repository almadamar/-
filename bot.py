import os
import logging
import asyncio
import random
import importlib
import glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# --- [هام جداً للمشاريع الأخرى] ---
active_users = set() 

# ---------------- [1] الإعدادات ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# ---------------- [2] وظيفة التحقق ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ---------------- [3] المحرك الأساسي للتحميل ----------------
async def download_video(query, context, url, mode):
    msg = await query.edit_message_text("⏳ جاري التحميل (720p)...")
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'],
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
    except:
        await msg.edit_text("❌ فشل التحميل.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    active_users.add(uid) 
    
    if await is_subscribed(context.bot, uid):
        await update.message.reply_text("🚀 أرسل الرابط للتحميل المباشر.\nاستخدم /stats للإحصائيات أو /broadcast للإذاعة (للمطور).")
    else:
        btn = [[InlineKeyboardButton("📢 اشترك هنا", url=CHANNEL_LINK)], [InlineKeyboardButton("✅ اشتركت", callback_data="check")]]
        await update.message.reply_text("⚠️ اشترك أولاً:", reply_markup=InlineKeyboardMarkup(btn))

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, update.effective_user.id): return
    
    link_id = str(random.randint(100, 999))
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو", callback_data=f"vid|{link_id}"), InlineKeyboardButton("🎵 صوت", callback_data=f"aud|{link_id}")]]
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

# ---------------- [4] نظام الربط التلقائي ----------------
def load_plugins(app):
    for plugin_file in glob.glob("plugin_*.py"):
        module_name = plugin_file[:-3]
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            if hasattr(module, "setup"):
                module.setup(app)
                print(f"✅ تم ربط المشروع الإضافي: {module_name}")
        except Exception as e:
            print(f"❌ خطأ في تحميل {module_name}: {e}")

# ---------------- [5] التشغيل ----------------
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
