import os, yt_dlp, asyncio, time
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- البيانات التي زودتني بها ---
BOT_TOKEN = "8539861357:AAG-GMmy5AGYpZAQ14ZeNymnAYlTjeZnKUM"
OWNER_ID = 162459553
# تم تحويل رابط القناة إلى المعرف البرمجي الخاص بها
MUSIC_CHANNEL = "@Musiciqh" 

# إعدادات التحميل لمحاولة تجنب حظر يوتيوب في سيرفرات Render
YDL_OPTS = {
    'format': 'bestaudio/best',
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
}

async def auto_download_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return
    
    # حماية: البوت لا يستجيب إلا لمنار (صاحب الحساب 162459553)
    if update.effective_user.id != OWNER_ID:
        return

    status_msg = await update.message.reply_text("📡 جاري فحص الرابط والتحميل تلقائياً إلى @Musiciqh ... 🎵")

    if not os.path.exists('temp'): os.makedirs('temp')

    def run_yt_dlp():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info: return False
                
                # التعامل مع فيديو واحد أو قائمة تشغيل
                entries = info.get('entries', [info])
                for entry in entries:
                    if not entry: continue
                    file_path = ydl.prepare_filename(entry).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                    
                    # إنشاء حلقة أحداث لإرسال الملف
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=MUSIC_CHANNEL,
                        audio=open(file_path, 'rb'),
                        caption=f"🎵 **{entry.get('title')}**\n👤 #{entry.get('uploader', 'Unknown').replace(' ', '_')}"
                    ))
                    
                    # حذف الملف بعد الرفع لتوفير مساحة السيرفر
                    if os.path.exists(file_path): os.remove(file_path)
                    time.sleep(7) # تأخير بسيط لتجنب الحظر
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    # تشغيل عملية التحميل في خلفية الكود لضمان عدم توقف البوت
    success = await asyncio.to_thread(run_yt_dlp)
    
    if success:
        await status_msg.edit_text("✅ اكتمل الرفع بنجاح إلى القناة!")
    else:
        await status_msg.edit_text("❌ فشل التحميل. يوتيوب يطلب كوكيز أو قام بحظر السيرفر.")

def main():
    # تشغيل البوت مع مسح أي طلبات قديمة (لحل مشكلة التداخل)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_download_process))
    
    print("🚀 بوت @ubgo3_bot يعمل الآن بنجاح...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
