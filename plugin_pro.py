import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK, DOWNLOAD_DIR

# إعدادات تحافظ على شكل الفيديو الأصلي (طولي، عرضي، سينمائي)
YDL_OPTS = {
    # تحميل فيديو MP4 بدقة 720p كحد أقصى مع الحفاظ على نسبة الطول للعرض الأصلية
    'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best',
    'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
    'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
    }],
    # أوامر تضمن عدم التلاعب بمقاسات الفيديو (No scaling/stretching)
    'postprocessor_args': [
        '-vcodec', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '23',           # توازن ممتاز بين الجودة وحجم الملف
        '-preset', 'medium',
        '-aspect', 'copy'       # الحفاظ على أبعاد الفيديو الأصلية كما هي
    ],
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
                await update.message.reply_video(
                    video=f, 
                    caption=f"🎬: {title}\n📢 {CHANNEL_LINK}", 
                    reply_markup=InlineKeyboardMarkup(kb),
                    supports_streaming=True 
                )
            os.remove(path)
            await status.delete()
        else:
            await status.edit_text("❌ لم يتم العثور على ملف الفيديو.")

    except Exception as e:
        print(f"Pro DL Error: {e}")
        await status.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً أو غير مدعوم حالياً.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl))
