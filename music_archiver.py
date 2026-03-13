import os, yt_dlp, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MUSIC_STORAGE = "@Musiciqh" 
OFFICIAL_CHAN = "@UpGo2"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    
    # رسالة فحص صامتة لمعرفة نوع المحتوى
    loading_msg = await update.message.reply_text("🔍 جاري فحص الرابط...")

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            # تحديد هل الرابط صوتي أصلي (مثل ساوند كلاود)
            is_audio = info.get('extractor') in ['soundcloud', 'audiomack'] or 'audio' in info.get('format', '').lower()

        if is_audio:
            # خيار الأرشفة للصوت فقط (يذهب للقناة)
            kb = [[InlineKeyboardButton("🎵 أرشفة الأغنية للموسيقى", callback_data=f"aud_{url}")]]
            text = "🎶 **رابط صوتي مكتشف!**\nسيتم نقل الأغنية إلى أرشيف القناة العام."
        else:
            # خيار التحميل المباشر للفيديو (يبقى في البوت)
            kb = [[InlineKeyboardButton("🎬 تحميل الفيديو الآن", callback_data=f"vid_{url}")]]
            text = "🎬 **رابط فيديو مكتشف!**\nسيتم إرسال الفيديو لك هنا مباشرة بالأبعاد الأصلية."

        await loading_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    except Exception:
        await loading_msg.edit_text("⚠️ عذراً، لم أستطع تحديد نوع المحتوى.")

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data[4:]
    is_audio_task = data.startswith("aud_")
    chat_id = query.message.chat_id
    
    await query.edit_message_reply_markup(reply_markup=None) 
    
    # تفعيل الحالة التفاعلية (يتم إرسال فيديو / صوت)
    action = "upload_audio" if is_audio_task else "upload_video"
    try: await context.bot.send_chat_action(chat_id=chat_id, action=action)
    except: pass

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚙️ جاري التجهيز {'للأرشفة' if is_audio_task else 'للتحميل المباشر'}...\n\n▒▒▒▒▒▒▒▒▒▒ 0%",
        parse_mode="Markdown"
    )

    def process_and_send():
        try:
            tmp_dir = "/tmp"
            opts = {
                'format': 'bestaudio/best' if is_audio_task else 'bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]/best',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                if os.path.exists(file_path):
                    # الفرق الجوهري هنا:
                    # إذا كان صوتاً: يذهب لـ MUSIC_STORAGE
                    # إذا كان فيديو: يذهب لـ chat_id (المستخدم)
                    target = MUSIC_STORAGE if is_audio_task else chat_id
                    method = "sendAudio" if is_audio_task else "sendVideo"
                    
                    send_api = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
                    with open(file_path, 'rb') as f:
                        requests.post(send_api, data={'chat_id': target, 'caption': f"✅ تم بواسطة: @Down2024_bot"}, files={('audio' if is_audio_task else 'video'): f})
                    
                    os.remove(file_path)
                    return True, info.get('title')
            return False, "فشل الاستخراج"
        except Exception as e: return False, str(e)

    success, title = process_and_send()
    if success:
        if is_audio_task:
            await status_msg.edit_text(f"🏁 **تمت الأرشفة!**\nنقلت الأغنية `{title}` إلى قناة الموسيقى بنجاح.",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎧 قناة الموسيقى", url="https://t.me/Musiciqh")]]))
        else:
            await status_msg.delete() # حذف رسالة الحالة وإرسال الفيديو تم بالفعل للمستخدم
    else:
        await status_msg.edit_text(f"⚠️ خطأ: {title}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(aud_|vid_)"), group=2)
