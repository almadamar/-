import os, yt_dlp, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config_data import CHANNEL_LINK, DOWNLOAD_DIR

async def audio_detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return

    # معرف فريد للملف الصوتي لعدم التداخل
    a_id = f"aud_{random.randint(1000, 9999)}"
    context.user_data[a_id] = url
    
    kb = [[InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"down_aud|{a_id}")]]
    
    # رسالة عرض ميزة الصوت بشكل مستقل
    await update.message.reply_text("🎧 خيار إضافي: هل تود الحصول على الصوت فقط؟", 
                                  reply_markup=InlineKeyboardMarkup(kb))

async def process_audio_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data or not query.data.startswith("down_aud|"): return
    
    await query.answer("🎧 جاري معالجة الصوت... يرجى الانتظار")
    _, a_id = query.data.split("|")
    url = context.user_data.get(a_id)
    
    if not url:
        await query.edit_message_text("❌ عذراً، انتهت صلاحية الطلب.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/audio_%(id)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        def dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

        path = await asyncio.to_thread(dl)
        
        with open(path, 'rb') as f:
            await query.message.reply_audio(audio=f, caption=f"🎵 تم استخراج الصوت\n📢 {CHANNEL_LINK}")
        
        if os.path.exists(path): os.remove(path)
        await query.message.delete()
    except Exception as e:
        await query.message.reply_text("❌ فشل استخراج الصوت من هذا الرابط.")

def setup(app):
    # نستخدم Group=1 ليعمل الملحق بالتوازي مع ملحقات الفيديو في Group=0
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, audio_detector), group=1)
    app.add_handler(CallbackQueryHandler(process_audio_only))
