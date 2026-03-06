import os, logging, asyncio, random, yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- [الإعدادات] ---
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)

# --- [دالة التحميل] ---
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not (url.startswith("http") or url.startswith("www")): return
    
    msg = await update.message.reply_text("⏳ جاري تحميل الفيديو...")
    
    # إعدادات مبسطة جداً لتحميل فيديو MP4 جاهز دون الحاجة لـ FFmpeg
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': 45 * 1024 * 1024  # حد 45 ميجا لتناسب سيرفر Render المجاني
    }
    
    try:
        # تنفيذ التحميل
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        # إرسال الفيديو
        with open(file_path, 'rb') as f:
            await update.message.reply_video(video=f, caption="✅ تم التحميل بواسطة @Down2024_bot")
        
        # حذف الملف من السيرفر فوراً لتوفير المساحة
        if os.path.exists(file_path): os.remove(file_path)
        await msg.delete()
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await msg.edit_text("❌ فشل التحميل. قد يكون الرابط محمي أو حجمه كبير جداً.")

# --- [تشغيل البوت] ---
def main():
    # بناء التطبيق مع حل مشكلة الـ Conflict برمجياً
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🚀 أرسل رابط الفيديو للتحميل مباشرة.")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🚀 البوت يعمل الآن (فيديو فقط)...")
    
    # drop_pending_updates=True تمسح أي تداخل قديم وتمنع خطأ Conflict
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
