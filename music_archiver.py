import os, yt_dlp, asyncio, time
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

# --- الإعدادات الموسيقية ---
ADMIN_ID = 162459553
TARGET_CHANNEL = "@Musiciqh"

# إعدادات معزولة تماماً لمحرك الأغاني لتجنب تعارض الـ IP والملفات
SONG_ENGINE_OPTS = {
    'format': 'bestaudio/best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
    'outtmpl': 'temp/track_%(title)s.%(ext)s', # تمييز اسم الملف المؤقت
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
}

async def music_storage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text
    
    # يعمل فقط عند إرسال رمز النغمة 🎵 قبل الرابط لضمان عدم التداخل مع بوت التحميل القديم
    if not msg_text or not msg_text.startswith("🎵 "):
        return
        
    if update.effective_user.id != ADMIN_ID:
        return

    song_url = msg_text.replace("🎵 ", "").strip()
    if not song_url.startswith("http"):
        await update.message.reply_text("⚠️ يرجى إرسال رابط صحيح بعد الرمز، مثال:\n 🎵 https://youtube.com/...")
        return

    info_msg = await update.message.reply_text("🎼 [محرك الأغاني]: جاري الأرشفة إلى القناة...")

    def start_music_download():
        try:
            if not os.path.exists('temp'): os.makedirs('temp')
            with yt_dlp.YoutubeDL(SONG_ENGINE_OPTS) as ydl:
                info = ydl.extract_info(song_url, download=True)
                entries = info.get('entries', [info])
                for entry in entries:
                    if not entry: continue
                    # الحصول على مسار الملف وتحويله لـ mp3
                    file_path = ydl.prepare_filename(entry).rsplit('.', 1)[0] + '.mp3'
                    
                    # إنشاء حلقة إرسال منفصلة
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=TARGET_CHANNEL,
                        audio=open(file_path, 'rb'),
                        caption=f"🎧 تم الحفظ في الأرشيف\n📌 {entry.get('title')}\n👤 #المصدر"
                    ))
                    
                    # تنظيف السيرفر
                    if os.path.exists(file_path): os.remove(file_path)
                    time.sleep(5)
                return True
        except Exception as e:
            print(f"Music Engine Error: {e}")
            return False

    # تنفيذ المهمة في Thread منفصل لعدم تجميد البوت
    success = await asyncio.to_thread(start_music_download)
    
    if success:
        await info_msg.edit_text("✅ تمت الأرشفة الموسيقية بنجاح!")
    else:
        await info_msg.edit_text("❌ عذراً، محرك الأغاني واجه مشكلة (قد يكون حظراً من يوتيوب).")

# دالة الربط (يتم استدعاؤها من ملف main.py)
def setup_music_module(application):
    # الفلتر يتحسس فقط للرسائل التي تبدأ بـ 🎵 ورابط
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^🎵 http'), music_storage_handler))
