import os, yt_dlp, asyncio, time
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import config

# إعدادات متقدمة لمحاولة الالتفاف على حظر يوتيوب في Render
YDL_OPTS = {
    'format': 'bestaudio/best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0', # محاولة استخدام IPv4 الافتراضي للسيرفر
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl': 'temp/%(title)s.%(ext)s',
}

async def auto_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return
    
    # التحقق من الهوية (صاحب البوت)
    if update.effective_user.id != config.OWNER_ID: return

    # رسالة تأكيد فورية (لو لم تظهر فهذا يعني أن البوت متوقف تماماً)
    status_msg = await update.message.reply_text("📡 جاري محاولة كسر الحظر وتحميل الرابط تلقائياً...")

    if not os.path.exists('temp'): os.makedirs('temp')

    def run_dl():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                # محاولة استخراج الرابط مع تجاهل الحظر الجغرافي
                info = ydl.extract_info(url, download=True)
                if not info: return False
                
                entries = info.get('entries', [info])
                for entry in entries:
                    if not entry: continue
                    file_path = ydl.prepare_filename(entry).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=config.MUSIC_CHANNEL_ID,
                        audio=open(file_path, 'rb'),
                        caption=f"🎵 {entry.get('title')}"
                    ))
                    if os.path.exists(file_path): os.remove(file_path)
                    time.sleep(5)
                return True
        except Exception as e:
            print(f"Error Detail: {e}")
            return False

    success = await asyncio.to_thread(run_dl)
    if not success:
        await status_msg.edit_text("❌ فشل: يوتيوب لا يزال يحظر السيرفر. (الحل الوحيد المتبقي هو ملف الكوكيز أو تغيير السيرفر).")
    else:
        await status_msg.edit_text("✅ تم التحميل بنجاح!")

def main():
    # استخدام التوكن من ملف config
    app = Application.builder().token(config.TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_download))
    print("🤖 البوت يعمل... جاري استقبال الروابط.")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
