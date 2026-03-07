import os, yt_dlp, asyncio
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # تأمين البيانات قبل التقسيم
    if not query.data or "|" not in query.data: return 

    try:
        mode, t_id = query.data.split("|") # السطر 25 المصلح
        url = context.user_data.get(t_id)
        if not url: return

        await query.answer("📥 جاري التحميل...")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f'downloads/%(id)s.%(ext)s', 'quiet': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(lambda: ydl.extract_info(url, download=True))
            path = ydl.prepare_filename(info)
            
        with open(path, 'rb') as f:
            await query.message.reply_audio(audio=f, caption="✅ تم بواسطة بوت أنمار")
        if os.path.exists(path): os.remove(path)

    except Exception as e: print(f"Download Error: {e}")

def setup(app):
    app.add_handler(CallbackQueryHandler(process_download))
