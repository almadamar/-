import os, yt_dlp, asyncio, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# توكن البوت الثاني (استخدمه هنا كجسر إرسال فقط لتخفيف الضغط)
SENDING_BOT_TOKEN = "7547192938:AAHLnK837Vl6T_iAasD_z0W5YwYpizT8eW0"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if any(p in url.lower() for p in ["soundcloud", "spotify", "audiomack", "music"]):
        kb = [[InlineKeyboardButton("🎵 أرشفة نهائية ومضمونة", callback_data=f"go_{url}")]]
        await update.message.reply_text("📥 جاهز للنقل إلى @Musiciqh؟", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("go_", "")
    await query.answer()
    status = await query.edit_message_text("🚀 جاري التحميل والنقل المباشر... (لحظات)")

    def download_and_ship():
        try:
            path = "/tmp/music_file.mp3"
            opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': '/tmp/music_file.%(ext)s',
                'quiet': True, 'noplaylist': True
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'New Track')

            # استخدام Requests (طريقة النقل السريع) لتجنب تعليق السيرفر
            if os.path.exists(path):
                url_api = f"https://api.telegram.org/bot{SENDING_BOT_TOKEN}/sendAudio"
                with open(path, 'rb') as audio:
                    payload = {'chat_id': '@Musiciqh', 'caption': f"🎧 {title}\n✅ @Musiciqh"}
                    files = {'audio': audio}
                    r = requests.post(url_api, data=payload, files=files)
                return r.status_code == 200, title
            return False, "الملف لم يُحفظ"
        except Exception as e:
            return False, str(e)

    success, message = await asyncio.to_thread(download_and_ship)
    
    if success:
        await status.edit_text(f"✅ تمت الأرشفة بنجاح: {message}")
    else:
        await status.edit_text(f"❌ عذراً، حدث خطأ: {message}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^go_"), group=2)
