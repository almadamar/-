import os, yt_dlp, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

logger = logging.getLogger(__name__)

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    # تشغيل الفحص على روابط الموسيقى فقط
    if any(p in url.lower() for p in ["soundcloud", "spotify", "apple", "deezer", "audiomack", "music.youtube"]):
        kb = [[InlineKeyboardButton("🔍 أرشِف واكشف المسار", callback_data=f"scan_{url}")]]
        await update.message.reply_text("📂 نظام الجرد والتحميل جاهز..", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("scan_", "")
    await query.answer()
    status = await query.edit_message_text("⚙️ جاري التحميل + جرد ملفات السيرفر...")

    def core_logic():
        try:
            # استخدام المجلد المؤقت للنظام /tmp لأنه الوحيد المضمون للكتابة في Render
            target_dir = "/tmp"
            if not os.path.exists(target_dir): target_dir = os.getcwd()
            
            file_id = "final_output"
            opts = {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': f'{target_dir}/{file_id}.%(ext)s',
                'quiet': True,
                'noplaylist': True
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Music File')

            expected_path = f"{target_dir}/{file_id}.mp3"
            
            # --- نظام الفحص (Scanner) الذي طلبته ---
            files_found = os.listdir(target_dir)
            report = f"📍 المسار: {target_dir}\n📦 محتوى المجلد:\n" + "\n".join([f"- {f}" for f in files_found if f.endswith(('.mp3', '.m4a', '.webm'))])

            if os.path.exists(expected_path):
                # تعديل الحقوق
                audio = MP3(expected_path, ID3=ID3)
                try: audio.add_tags()
                except: pass
                audio.tags.add(TIT2(encoding=3, text=title))
                audio.tags.add(TPE1(encoding=3, text="@Musiciqh"))
                audio.save()
                return True, expected_path, title, report
            
            return False, None, None, f"⚠️ لم أجد الملف المطلوب.\n{report}"
            
        except Exception as e:
            return False, None, None, f"❌ خطأ تقني: {str(e)}"

    success, file_path, title, final_report = await asyncio.to_thread(core_logic)

    if success:
        try:
            with open(file_path, 'rb') as f:
                await context.bot.send_audio(
                    chat_id="@Musiciqh", 
                    audio=f, 
                    caption=f"🎧 {title}\n✅ @Musiciqh\n\n{final_report}" # يرسل التقرير في الكابشن للتأكد
                )
            await status.edit_text("✅ تمت الأرشفة بنجاح!")
            os.remove(file_path)
        except Exception as e:
            await status.edit_text(f"❌ فشل الإرسال للقناة: {e}\n\n{final_report}")
    else:
        await status.edit_text(final_report)

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^scan_"), group=2)
