import os, yt_dlp, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes

# استيراد CHANNEL_LINK من الملف المناسب
from config_data import CHANNEL_LINK

async def yt_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url: return
    
    # إشعار المستخدم بالبدء
    status = await update.message.reply_text("📺 جاري فحص رابط يوتيوب... يرجى الانتظار")
    
    t_id = f"yt_{random.randint(100, 999)}"
    context.user_data[t_id] = url

    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # التحميل في Thread منفصل لمنع التعليق
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        kb = [
            [InlineKeyboardButton("🚀 مشاركة عبر البوت", switch_inline_query=f"@{context.bot.username}")],
            [InlineKeyboardButton("🎵 استخراج الصوت MP3", callback_data=f"ya|{t_id}")]
        ]

        if os.path.exists(path):
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    video=f, 
                    caption=f"🎬 تم التحميل بنجاح\n📢 {CHANNEL_LINK}", 
                    reply_markup=InlineKeyboardMarkup(kb)
                )
            os.remove(path)
            await status.delete()
        else:
            await status.edit_text("❌ لم يتم العثور على الملف بعد التحميل.")

    except Exception as e:
        print(f"YT Error: {e}")
        await status.edit_text("❌ عذراً، هذا الرابط غير مدعوم حالياً أو الفيديو طويل جداً.")

def setup(app):
    # تحسين Regex لضمان التقاط كافة روابط يوتيوب وعزلها في المجموعة 1
    yt_filter = filters.Regex(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')
    app.add_handler(MessageHandler(yt_filter, yt_dl), group=1)
