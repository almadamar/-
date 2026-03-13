import os, yt_dlp, asyncio, time
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import config

# إعدادات التحميل (بدون كوكيز مع تمويه المتصفح)
YDL_OPTS = {
    'format': 'bestaudio/best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }, {'key': 'FFmpegMetadata'}],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'ignoreerrors': True,
    'quiet': True,
    'nocheckcertificate': True,
}

async def handle_auto_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    # التأكد أن المستخدم هو صاحب البوت فقط
    if update.effective_user.id != config.OWNER_ID: return

    status_msg = await update.message.reply_text("🔎 تم استلام الرابط.. جاري الفحص والتحميل التلقائي للقناة 🎵")

    if not os.path.exists('temp'): os.makedirs('temp')

    def process():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                # استخراج المعلومات (سواء كان فيديو واحد أو قائمة)
                info = ydl.extract_info(url, download=False)
                if not info: return "error"
                
                # تحويله إلى قائمة من الإدخالات (Entries)
                entries = info.get('entries', [info])
                
                for entry in entries:
                    if not entry: continue
                    # تحميل الملف
                    data = ydl.extract_info(entry['url'], download=True)
                    path = ydl.prepare_filename(data).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                    
                    # إرسال الملف للقناة الموسيقية مباشرة
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=config.MUSIC_CHANNEL_ID,
                        audio=open(path, 'rb'),
                        caption=f"🎵 **{data.get('title')}**\n👤 #{data.get('uploader', 'Unknown').replace(' ', '_')}"
                    ))
                    
                    # حذف الملف المؤقت لتوفير المساحة
                    if os.path.exists(path): os.remove(path)
                    
                    # انتظار 10 ثوانٍ لتجنب الحظر
                    time.sleep(10)
                return "success"
        except Exception as e:
            print(f"Error: {e}")
            return "error"

    result = await asyncio.to_thread(process)
    if result == "success":
        await status_msg.edit_text("✅ تم الانتهاء من تحميل كافة المحتويات إلى القناة!")
    else:
        await status_msg.edit_text("❌ حدث خطأ أثناء التحميل (قد يكون الرابط محظوراً أو غير صحيح).")

def main():
    # استخدام التوكن الخاص بك من ملف config
    app = Application.builder().token(config.TOKEN).build()
    
    # البوت الآن سيراقب أي نص (رابط) يتم إرساله ويقوم بتحميله تلقائياً
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auto_download))
    
    print("🤖 البوت يعمل الآن بنظام التحميل التلقائي للروابط...")
    app.run_polling()

if __name__ == '__main__':
    main()
