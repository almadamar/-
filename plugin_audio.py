import os, yt_dlp, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes

async def handle_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if any(x in url for x in ["youtube.com", "youtu.be"]): return # يترك الرابط لملحق يوتيوب
    
    t_id = f"sc_{random.randint(100, 999)}"
    context.user_data[t_id] = url
    btns = [[InlineKeyboardButton("📥 تحميل الفيديو", callback_data=f"sv|{t_id}")]]
    await update.message.reply_text("📱 تم اكتشاف رابط: اختر التحميل", reply_markup=InlineKeyboardMarkup(btns))

async def process_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data or not query.data.startswith("sv|"): return
    await query.answer()
    _, t_id = query.data.split("|")
    url = context.user_data.get(t_id)
    
    ydl_opts = {'format': 'best', 'outtmpl': f'downloads/%(id)s.%(ext)s', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await asyncio.to_thread(lambda: ydl.extract_info(url, download=True))
        path = ydl.prepare_filename(info)
        with open(path, 'rb') as f: await query.message.reply_video(f)
        os.remove(path)

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_social))
    app.add_handler(CallbackQueryHandler(process_social))
