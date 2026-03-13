import os, yt_dlp, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, COMM

# إعدادات البوت الثاني والقناة
STORAGE_CHANNEL_ID = "@Musiciqh" 
BOT_USERNAME = "AutoMusicHubBot"

# إعدادات التحميل (جودة احترافية)
SONG_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320'
    }],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'quiet': True,
}

def apply_rights(file_path, title):
    try:
        audio = MP3(file_path, ID3=ID3)
        try: audio.add_tags()
        except: pass
        audio.tags.add(TIT2(encoding=3, text=title)) 
        audio.tags.add(TPE1(encoding=3, text="@Musiciqh")) 
        audio.tags.add(COMM(encoding=3, lang='eng', desc='desc', text="Archived by @AutoMusicHubBot"))
        audio.save()
    except: pass

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # تجاهل يوتيوب وتيك توك لترك العمل للبوت الأساسي
    if any(x in url.lower() for x in ["youtube.com", "youtu.be", "tiktok.com"]):
        return 

    kb = [[InlineKeyboardButton("🎵 حفظ في أرشيف @Musiciqh", callback_data=f"arch_{url}")]]
    await update.message.reply_text(f"✨ نظام الأرشفة الذكي جاهز..\nسأقوم بتغيير الحقوق لـ @Musiciqh ورفعها فوراً.", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    status = await query.edit_message_text("⏳ جاري سحب الصوت وتعديل الحقوق...")

    def process():
        try:
            with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Music_File')
                path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                apply_rights(path, title)
                return True, path, title
        except Exception as e: return False, str(e), None

    success, path, title = await asyncio.to_thread(process)
    if success:
        with open(path, 'rb') as f:
            await context.bot.send_audio(chat_id=STORAGE_CHANNEL_ID, audio=f, caption=f"🎧 {title}\n✅ تمت الأرشفة في @Musiciqh")
        await status.edit_text("🏁 تمت الأرشفة بنجاح!")
        os.remove(path)
    else:
        await status.edit_text(f"❌ خطأ: {path}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click), group=2)
