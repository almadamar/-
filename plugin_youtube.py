import asyncio, yt_dlp, os, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, CallbackQueryHandler, ContextTypes

DOWNLOAD_DIR = 'downloads'

async def handle_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # كشف روابط يوتيوب بمختلف أشكالها
    if not any(x in url for x in ["youtube.com", "youtu.be"]): return
    
    t_id = f"yt_{random.randint(100, 999)}"
    context.user_data[t_id] = url
    
    btns = [[
        InlineKeyboardButton("🎬 فيديو (720p)", callback_data=f"yv|{t_id}"),
        InlineKeyboardButton("🎵 صوت (MP3)", callback_data=f"ya|{t_id}")
    ]]
    await update.message.reply_text("📺 يوتيوب المطور: اختر الصيغة:", reply_markup=InlineKeyboardMarkup(btns))

async def process_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith(("yv|", "ya|")): return
    await query.answer()
    
    mode, t_id = query.data.split("|")
    url = context.user_data.get(t_id)
    msg = await query.edit_message_text("⏳ جاري كسر حماية يوتيوب والتحميل...")
    
    ydl_opts = {
        'nocheckcertificate': True,
        'quiet': True,
        'outtmpl': f'{DOWNLOAD_DIR}/yt_%(id)s.%(ext)s',
        # الثغرة الجديدة: إجبار يوتيوب على استخدام مشغل الأندرويد المخفف
        'user_agent': 'com.google.android.youtube/19.05.36 (Linux; U; Android 11) Mobile/Creator',
        'referer': 'https://www.google.com/',
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['webpage', 'ios']
            }
        },
        'format': 'best[height<=720][ext=mp4]/best' if mode == 'yv' else 'bestaudio/best'
    }

    try:
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        with open(path, 'rb') as f:
            if mode == 'yv': await query.message.reply_video(f, caption="✅ تم بنجاح")
            else: await query.message.reply_audio(f, caption="✅ تم استخراج الصوت")
        
        if os.path.exists(path): os.remove(path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text("❌ يوتيوب يرفض بشدة.\n💡 جرب مسح ملف 'cookies.txt' إذا كنت تستخدمه، أو انتظر قليلاً.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'youtube|youtu\.be'), handle_youtube_url))
    app.add_handler(CallbackQueryHandler(process_youtube))
