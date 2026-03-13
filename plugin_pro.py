import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK, DOWNLOAD_DIR

YDL_OPTS = {
    'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best',
    'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
    'postprocessors': [{'key': 'FFmpegVideoConvertor','preferedformat': 'mp4'}],
    'postprocessor_args': ['-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'veryfast'],
    'prefer_ffmpeg': True,
}

async def direct_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http") or "youtube" in url:
        return
    
    status = await update.message.reply_text("⏳ جاري التحميل بالأبعاد الأصلية (720p)...")

    try:
        def download():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get('title', 'Video')

        path, title = await asyncio.to_thread(download)
        
        kb = [
            [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"sa|{os.path.basename(path)}")],
            [InlineKeyboardButton("🚀 مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{context.bot.username}")]
        ]

        if os.path.exists(path):
            with open(path, 'rb') as f:
                await update.message.reply_video(video=f, caption=f"🎬: {title}\n📢 {CHANNEL_LINK}", reply_markup=InlineKeyboardMarkup(kb), supports_streaming=True)
            os.remove(path)
            await status.delete()
        else:
            await status.edit_text("❌ حدث خطأ: لم يتم العثور على الملف.")
    except Exception as e:
        await status.edit_text("❌ فشل التحميل.")

def setup(app):
    # تم العزل في المجموعة 1 لعدم التصادم مع البوت الجديد
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl), group=1)
