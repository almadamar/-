import asyncio, yt_dlp, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    # تخزين الرابط مؤقتاً
    t_id = str(random.randint(100, 999))
    context.user_data[t_id] = url
    
    btns = [[
        InlineKeyboardButton("🎬 فيديو 720p", callback_data=f"v|{t_id}"),
        InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a|{t_id}")
    ]]
    await update.message.reply_text("اختر الصيغة:", reply_markup=InlineKeyboardMarkup(btns))

async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mode, t_id = query.data.split("|")
    url = context.user_data.get(t_id)

    msg = await query.edit_message_text("⏳ جاري التحميل...")
    
    opts = {
        'nocheckcertificate': True, 'quiet': True,
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'format': 'best[height<=720][ext=mp4]/best' if mode == 'v' else 'bestaudio/best'
    }

    try:
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(opts).extract_info(url, download=True))
        path = yt_dlp.YoutubeDL(opts).prepare_filename(info)
        with open(path, 'rb') as f:
            if mode == 'v': await query.message.reply_video(f)
            else: await query.message.reply_audio(f)
        if os.path.exists(path): os.remove(path)
        await msg.delete()
    except: await msg.edit_text("❌ فشل.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(start_download))
