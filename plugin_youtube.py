import asyncio, yt_dlp, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes

async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not any(x in url for x in ["youtube.com", "youtu.be"]): return
    
    t_id = f"yt_{random.randint(100, 999)}"
    context.user_data[t_id] = url
    btns = [[InlineKeyboardButton("🎬 فيديو يوتيوب", callback_data=f"yv|{t_id}"),
             InlineKeyboardButton("🎵 صوت MP3", callback_data=f"ya|{t_id}")]]
    await update.message.reply_text("📺 اختر صيغة التحميل من يوتيوب:", reply_markup=InlineKeyboardMarkup(btns))

async def process_yt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data or not query.data.startswith(("yv|", "ya|")): return
    await query.answer()
    mode, t_id = query.data.split("|")
    url = context.user_data.get(t_id)
    
    ydl_opts = {
        'format': 'best[height<=720]' if mode == 'yv' else 'bestaudio/best',
        'outtmpl': f'downloads/%(id)s.%(ext)s',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await asyncio.to_thread(lambda: ydl.extract_info(url, download=True))
        path = ydl.prepare_filename(info)
        with open(path, 'rb') as f:
            if mode == 'yv': await query.message.reply_video(f)
            else: await query.message.reply_audio(f)
        os.remove(path)

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'youtube|youtu\.be'), handle_youtube))
    app.add_handler(CallbackQueryHandler(process_yt))
