import os, yt_dlp, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, COMM
from config_data import DOWNLOAD_DIR # استيراد المجلد فقط

logger = logging.getLogger(__name__)

SONG_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320'
    }],
    # استخدام اسم بسيط للملف لتجنب مشاكل الرموز
    'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s', 
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
    music_platforms = ["soundcloud.com", "spotify.com", "apple.com", "deezer.com", "audiomack.com", "anghami.com", "music.youtube", "pin.it", "pinterest.com"]
    
    if any(p in url.lower() for p in music_platforms):
        kb = [[InlineKeyboardButton("🎵 أرشفة في @Musiciqh", callback_data=f"arch_{url}")]]
        await update.message.reply_text("📥 تم رصد رابط موسيقي.. جاهز للأرشفة؟", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    status = await query.edit_message_text("⏳ جاري التحميل والمعالجة...")

    def process():
        try:
            if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
            with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info: info = info['entries'][0]
                title = info.get('title', 'Music_File')
                # المسار باستخدام ID الفيديو لضمان عدم ضياع الملف
                path = os.path.join(DOWNLOAD_DIR, f"{info['id']}.mp3")
                if os.path.exists(path):
                    apply_rights(path, title)
                    return True, path, title
                return False, "الملف لم يتم العثور عليه بعد التحويل", None
        except Exception as e:
            return False, str(e), None

    success, result, title = await asyncio.to_thread(process)

    if success:
        try:
            with open(result, 'rb') as f:
                # محاولة الإرسال باستخدام المعرف النصي مباشرة
                await context.bot.send_audio(
                    chat_id="@Musiciqh", 
                    audio=f, 
                    caption=f"🎧 {title}\n✅ تمت الأرشفة في @Musiciqh"
                )
            await status.edit_text("🏁 تم الإرسال بنجاح إلى @Musiciqh")
        except Exception as e:
            logger.error(f"❌ فشل الإرسال: {e}")
            await status.edit_text(f"❌ تم التحميل ولكن فشل الإرسال للقناة.\nالسبب: {e}")
        
        if os.path.exists(result): os.remove(result)
    else:
        await status.edit_text(f"❌ فشل التحميل: {result}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
