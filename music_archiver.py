import os, yt_dlp, asyncio, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    platforms = ["soundcloud", "spotify", "audiomack", "apple.com", "deezer", "anghami", "music.youtube"]
    if any(p in url.lower() for p in platforms):
        # أزرار معاينة قبل التحميل
        kb = [
            [InlineKeyboardButton("📥 بدء الأرشفة في القناة", callback_data=f"arch_{url}")],
            [InlineKeyboardButton("📢 زيارة القناة @Musiciqh", url="https://t.me/Musiciqh")]
        ]
        await update.message.reply_text("🎵 تم رصد رابط موسيقي. هل تود أرشفته الآن؟", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.replace("arch_", "")
    await query.answer()
    
    status = await query.edit_message_text("⚡ جاري المعالجة والنقل للقناة... يرجى الانتظار.")

    def sync_process():
        try:
            tmp_dir = "/tmp"
            output_file = os.path.join(tmp_dir, f"track_{query.from_user.id}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': output_file + '.%(ext)s',
                'quiet': True, 'noplaylist': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Music Track')

            final_path = output_file + ".mp3"
            
            if os.path.exists(final_path):
                send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                # إضافة أزرار داخل القناة للعودة للبوت
                channel_kb = {"inline_keyboard": [[{"text": "🤖 العودة للبوت المحمل", "url": "https://t.me/Down2024_bot"}]]}
                
                with open(final_path, 'rb') as audio:
                    payload = {
                        'chat_id': '@Musiciqh', 
                        'caption': f"🎧 {title}\n✅ تم الحفظ بواسطة @Down2024_bot",
                        'reply_markup': str(channel_kb).replace("'", '"')
                    }
                    files = {'audio': audio}
                    response = requests.post(send_url, data=payload, files=files)
                
                if os.path.exists(final_path): os.remove(final_path)
                return response.status_code == 200, title
            return False, "ملف التحميل مفقود"
        except Exception as e:
            return False, str(e)

    success, result = await asyncio.to_thread(sync_process)
    
    if success:
        # أزرار تظهر للمستخدم في البوت بعد النجاح
        success_kb = [
            [InlineKeyboardButton("🎧 استماع في القناة", url="https://t.me/Musiciqh")],
            [InlineKeyboardButton("🔄 تحميل أغنية أخرى", callback_data="new_search")]
        ]
        await status.edit_text(f"🏁 تمت الأرشفة بنجاح!\n🎵 العنوان: {result}", reply_markup=InlineKeyboardMarkup(success_kb))
    else:
        # حل مشكلة رسالة الخطأ الوهمية عبر إظهار السبب الحقيقي
        await status.edit_text(f"❌ تعذر الإكمال: {result}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
