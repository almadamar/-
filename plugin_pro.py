import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK # سنضع الروابط هنا

async def direct_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http") or "youtube" in url or "youtu.be" in url: return
    
    bot_info = await context.bot.get_me()
    status_msg = await update.message.reply_text("⏳ جاري التحميل التلقائي... دقة 720p")

    # إعدادات لمنع الانجمال وتثبيت الأبعاد 16:9
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
        'outtmpl': f'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True
    }

    try:
        # تشغيل في Thread منفصل لمنع توقف البوت
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        path = await asyncio.to_thread(run_dl)
        
        # حقوق النشر باسم البوت
        caption = f"✅ تم التحميل بواسطة: @{bot_info.username}\n📢 القناة: {CHANNEL_LINK}"
        kb = [[InlineKeyboardButton("🚀 مشاركة", switch_inline_query=f"@{bot_info.username}")],
              [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"to_mp3|{os.path.basename(path)}")]]

        with open(path, 'rb') as f:
            await update.message.reply_video(video=f, caption=caption, reply_markup=InlineKeyboardMarkup(kb), supports_streaming=True)
        
        await status_msg.delete()
        if os.path.exists(path): os.remove(path)
    except:
        await status_msg.edit_text("❌ عذراً، هذا الرابط غير مدعوم حالياً.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_download))
