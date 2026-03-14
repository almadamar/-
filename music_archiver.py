import os, yt_dlp, requests, json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# البيانات الثابتة
BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MUSIC_STORAGE = "@Musiciqh" 
SPECIAL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            is_audio = info.get('extractor') in ['soundcloud', 'audiomack'] or 'audio' in info.get('format', '').lower()

        if is_audio:
            # خيار الصوتيات: تظهر الرسالة مع زر الأرشفة
            kb = [[InlineKeyboardButton("🎵 أرشفة الأغنية للموسيقى", callback_data=f"aud_{url}")]]
            text = "🎶 **رابط صوتي مكتشف!**\nسيتم نقل الأغنية إلى أرشيف القناة العام."
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        else:
            # خيار الفيديوهات: تظهر الأزرار مباشرة بدون رسالة "تم رصد الفيديو"
            kb = [
                [InlineKeyboardButton("🎬 تحميل الفيديو الآن", callback_data=f"vid_{url}")],
                [InlineKeyboardButton("✨ انضم للقناة (رابط خاص)", url=SPECIAL_LINK)],
                [InlineKeyboardButton("🚀 مشاركة البوت", switch_inline_query="جرب هذا البوت الرهيب للتحميل!")]
            ]
            # إرسال الأزرار فقط مع نص بسيط أو فارغ حسب رغبتك (هنا وضعنا نقطة للجمالية)
            await update.message.reply_text("👇 اختر الإجراء المطلوب للفيديو:", reply_markup=InlineKeyboardMarkup(kb))

    except Exception:
        pass

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data[4:]
    is_audio_task = data.startswith("aud_")
    chat_id = query.message.chat_id
    
    await query.edit_message_reply_markup(reply_markup=None) 
    
    try: await context.bot.send_chat_action(chat_id=chat_id, action="upload_document")
    except: pass

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚙️ جاري {'الأرشفة' if is_audio_task else 'التحميل المباشر'}...",
        parse_mode="Markdown"
    )

    def download_and_dispatch():
        try:
            tmp_dir = "/tmp"
            opts = {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]/best' if not is_audio_task else 'bestaudio/best',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                if os.path.exists(file_path):
                    target = MUSIC_STORAGE if is_audio_task else chat_id
                    method = "sendAudio" if is_audio_task else "sendVideo"
                    
                    # حذف رابط القناة من الـ caption والاكتفاء بالأزرار في الأسفل
                    reply_markup = {
                        "inline_keyboard": [
                            [{"text": "✨ القناة الخاصة", "url": SPECIAL_LINK}],
                            [{"text": "🚀 مشاركة البوت", "url": "https://t.me/share/url?url=https://t.me/Down2024_bot"}]
                        ]
                    }
                    
                    send_api = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
                    with open(file_path, 'rb') as f:
                        payload = {
                            'chat_id': target, 
                            'caption': f"✅ تم بواسطة: @Down2024_bot", # تم حذف رابط القناة من هنا
                            'reply_markup': json.dumps(reply_markup)
                        }
                        files = {('audio' if is_audio_task else 'video'): f}
                        requests.post(send_api, data=payload, files=files)
                    
                    os.remove(file_path)
                    return True, info.get('title')
            return False, "فشل الاستخراج"
        except Exception as e: return False, str(e)

    success, title = download_and_dispatch()
    if success:
        if is_audio_task:
            await status_msg.edit_text(f"🏁 **تمت الأرشفة!**\nنقلت `{title}` للقناة.",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎧 قناة الموسيقى", url="https://t.me/Musiciqh")]]))
        else:
            await status_msg.delete() 
    else:
        await status_msg.edit_text(f"⚠️ خطأ: {title}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(aud_|vid_)"), group=2)
