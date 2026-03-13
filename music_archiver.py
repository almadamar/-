import os, yt_dlp, asyncio, logging, glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, COMM
from config_data import DOWNLOAD_DIR

logger = logging.getLogger(__name__)

# إعدادات ثابتة وقوية
SONG_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320'
    }],
    # نستخدم قالب بسيط جداً لضمان عدم ضياع المسار
    'outtmpl': f'{DOWNLOAD_DIR}/track_%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}

def apply_rights(file_path, title):
    try:
        audio = MP3(file_path, ID3=ID3)
        try: audio.add_tags()
        except: pass
        audio.tags.add(TIT2(encoding=3, text=title)) 
        audio.tags.add(TPE1(encoding=3, text="@Musiciqh")) 
        audio.tags.add(COMM(encoding=3, lang='eng', desc='desc', text="Archived by @Down2024_bot"))
        audio.save()
    except Exception as e:
        logger.error(f"⚠️ ميتاداتا: {e}")

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    # قائمة منصات الموسيقى
    if any(p in url.lower() for p in ["soundcloud.com", "spotify", "apple.com", "deezer", "audiomack", "anghami", "music.youtube"]):
        kb = [[InlineKeyboardButton("🎵 أرشفة في @Musiciqh", callback_data=f"arch_{url}")]]
        await update.message.reply_text("📥 تم رصد رابط موسيقي.. جاهز للأرشفة؟", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    status = await query.edit_message_text("⏳ جاري المعالجة النهائية وإرسال الملف...")

    def process_and_find():
        try:
            if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
            
            # 1. التحميل
            with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info: info = info['entries'][0]
                video_id = info.get('id')
                title = info.get('title', 'Music_File')

            # 2. البحث عن الملف الفعلي (أكثر طريقة مضمونة)
            # نبحث عن أي ملف في المجلد يحتوي على ID الفيديو وينتهي بـ mp3
            search_pattern = os.path.join(DOWNLOAD_DIR, f"*track_{video_id}*.mp3")
            found_files = glob.glob(search_pattern)

            if found_files:
                actual_path = found_files[0]
                apply_rights(actual_path, title)
                return True, actual_path, title
            
            return False, "تعذر تحديد مكان الملف بعد التحميل", None
        except Exception as e:
            return False, str(e), None

    success, result, title = await asyncio.to_thread(process_and_find)

    if success:
        try:
            with open(result, 'rb') as f:
                await context.bot.send_audio(
                    chat_id="@Musiciqh", 
                    audio=f, 
                    caption=f"🎧 {title}\n✅ تمت الأرشفة في @Musiciqh"
                )
            await status.edit_text("🏁 تم الإرسال بنجاح إلى القناة!")
        except Exception as e:
            await status.edit_text(f"❌ خطأ في الإرسال: {e}")
        
        # تنظيف المجلد
        if os.path.exists(result): os.remove(result)
    else:
        await status.edit_text(f"❌ فشل: {result}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
