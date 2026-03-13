import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK, DOWNLOAD_DIR

# إعدادات تضمن عدم تجمد الشاشة وسرعة التحميل
YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
    'merge_output_format': 'mp4',
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4', # إجبار الترميز المتوافق لمنع تجمد الصورة
    }],
}

async def direct_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http") or "youtube" in url:
        return
    
    status = await update.message.reply_text("⏳ جاري معالجة الفيديو بدقة عالية...")

    try:
        # التحميل في خلفية النظام لضمان عدم تعليق البوت
        def download():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get('title', 'Video')

        path, title = await asyncio.to_thread(download)
        
        # الأزرار المختصرة والمفيدة فقط
        kb = [
            [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"to_audio|{os.path.basename(path)}")],
            [InlineKeyboardButton("🚀 مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{context.bot.username}")]
        ]

        if os.path.exists(path):
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    video=f, 
                    caption=f"🎬: {title}\n📢 {CHANNEL_LINK}", 
                    reply_markup=InlineKeyboardMarkup(kb)
                )
            os.remove(path) # تنظيف السيرفر فوراً
            await status.delete()

    except Exception as e:
        print(f"Pro DL Error: {e}")
        await status.edit_text("❌ عذراً، فشل معالجة الفيديو. جرب رابطاً آخر.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl))
