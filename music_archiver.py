import os, yt_dlp, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

logger = logging.getLogger(__name__)

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    if any(p in url.lower() for p in ["soundcloud", "spotify", "apple", "deezer", "audiomack", "music.youtube"]):
        kb = [[InlineKeyboardButton("🎵 أرشفة وفحص المسارات", callback_data=f"arch_{url}")]]
        await update.message.reply_text("🔎 نظام الفحص جاهز.. اضغط للتحميل وكشف المسار:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    status = await query.edit_message_text("⏳ جاري التحميل.. سنقوم بجرد الملفات فوراً.")

    def process_with_scan():
        try:
            # التحميل في المجلد الحالي مباشرة
            current_dir = os.getcwd()
            opts = {
                'format': 'bestaudio/best',
                'default_search': 'ytsearch',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': os.path.join(current_dir, 'debug_track.%(ext)s'),
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Music')
                
            file_path = os.path.join(current_dir, 'debug_track.mp3')
            
            # --- ميزة كشف المسارات التي طلبتها ---
            all_files = os.listdir(current_dir)
            files_list_str = "\n".join([f"📄 {f}" for f in all_files[:15]]) # عرض أول 15 ملف فقط
            debug_info = f"📍 المجلد الحالي: {current_dir}\n📂 الملفات المكتشفة:\n{files_list_str}"

            if os.path.exists(file_path):
                # تطبيق الحقوق
                audio = MP3(file_path, ID3=ID3)
                try: audio.add_tags()
                except: pass
                audio.tags.add(TIT2(encoding=3, text=title))
                audio.tags.add(TPE1(encoding=3, text="@Musiciqh"))
                audio.save()
                return True, file_path, debug_info
            return False, debug_info, None
            
        except Exception as e:
            return False, f"⚠️ خطأ تقني: {str(e)}", None

    success, result, debug_msg = await asyncio.to_thread(process_with_scan)

    if success:
        try:
            with open(result, 'rb') as f:
                await context.bot.send_audio(chat_id="@Musiciqh", audio=f, caption=f"🎧 تم التحميل\n✅ @Musiciqh")
            await status.edit_text(f"🏁 تم الإرسال!\n\n🔍 تقرير المسار:\n{debug_msg}")
        except Exception as e:
            await status.edit_text(f"❌ خطأ إرسال: {e}\n\n📊 تقرير السيرفر:\n{debug_msg}")
        finally:
            if os.path.exists(result): os.remove(result)
    else:
        # إذا فشل التحميل، يطبع لك قائمة الملفات لتعرف أين ذهب الملف
        await status.edit_text(f"❌ لم يكتمل الإرسال.\n\n📊 جرد ملفات السيرفر:\n{debug_msg}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
