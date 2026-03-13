import os, yt_dlp, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK

async def yt_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status = await update.message.reply_text("📺 جاري معالجة فيديو يوتيوب...")
    
    t_id = f"yt_{random.randint(100, 999)}"
    context.user_data[t_id] = url

    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # تحميل الفيديو
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        # --- الأزرار تظهر هنا فقط عند نجاح التحميل ---
        kb = [
            [InlineKeyboardButton("🚀 مشاركة عبر البوت", switch_inline_query=f"@{context.bot.username}")],
            [InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"ya|{t_id}")]
        ]

        with open(path, 'rb') as f:
            await update.message.reply_video(
                video=f, 
                caption=f"🎬 يوتيوب جاهز\n📢 {CHANNEL_LINK}", 
                reply_markup=InlineKeyboardMarkup(kb)
            )

        await status.delete()
        if os.path.exists(path): os.remove(path)

    except Exception as e:
        print(f"YT DL Error: {e}")
        # رسالة فشل بدون أزرار
        await status.edit_text("❌ فشل تحميل فيديو يوتيوب. قد يكون الفيديو طويلاً جداً أو محمياً.")

def setup(app):
    # الفلتر الخاص بروابط يوتيوب فقط
    app.add_handler(MessageHandler(filters.Regex(r'youtube|youtu\.be'), yt_dl))
