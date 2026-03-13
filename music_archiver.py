import os, yt_dlp, asyncio, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# توكن البوت الأساسي (الذي ينتهي بـ 4NzI)
BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    # الكشف عن روابط الموسيقى
    platforms = ["soundcloud", "spotify", "audiomack", "apple.com", "deezer", "anghami"]
    if any(p in url.lower() for p in platforms):
        kb = [[InlineKeyboardButton("✅ أرشفة فورية (حل نهائي)", callback_data=f"arch_{url}")]]
        await update.message.reply_text("🎵 تم رصد الرابط. هل نبدأ الأرشفة الآن؟", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    
    status = await query.edit_message_text("⏳ جاري المعالجة... (لن يستغرق الأمر طويلاً)")

    def sync_process():
        try:
            # المسار المضمون في سيرفرات ريندر
            tmp_dir = "/tmp"
            output_file = os.path.join(tmp_dir, "final_track")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': output_file + '.%(ext)s',
                'quiet': True,
                'noplaylist': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Music Track')

            final_path = output_file + ".mp3"
            
            if os.path.exists(final_path):
                # إرسال الملف باستخدام Requests لتجنب RuntimeError
                send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                with open(final_path, 'rb') as audio:
                    payload = {'chat_id': '@Musiciqh', 'caption': f"🎧 {title}\n✅ تم الحفظ في @Musiciqh"}
                    files = {'audio': audio}
                    response = requests.post(send_url, data=payload, files=files)
                
                if response.status_code == 200:
                    return True, "تم الإرسال بنجاح!"
                return False, f"فشل في الإرسال: {response.text}"
            return False, "تعذر إنتاج ملف MP3"
        except Exception as e:
            return False, str(e)

    # تشغيل العملية في خيط منفصل تماماً
    success, result_msg = await asyncio.to_thread(sync_process)
    
    if success:
        await status.edit_text("🏁 تمت العملية بنجاح! تفقد القناة الآن.")
    else:
        await status.edit_text(f"❌ خطأ: {result_msg}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
