import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# إعدادات القنوات والتوكن
BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MUSIC_STORAGE = "@Musiciqh" # قناة تخزين الأغاني
OFFICIAL_CHAN = "@UpGo2"    # قناتك الرسمية

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    
    kb = [[InlineKeyboardButton("🌀 بدء الأرشفة الذكية", callback_data=f"arch_{url}")],
          [InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/UpGo2"),
           InlineKeyboardButton("📦 أرشيف الموسيقى", url="https://t.me/Musiciqh")]]
    
    await update.message.reply_text(
        "📥 **تم استلام الرابط بنجاح!**\nسيتم فحص المحتوى ونقله إلى نظام التخزين الخاص بنا 🚀",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
    )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.split("_", 1)[1]
    await query.answer()

    # تفعيل الحالة الخضراء تحت الاسم (يتم إرسال ملف...)
    try: await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_document")
    except: pass

    status_msg = await query.edit_message_text(
        "🔍 **جاري التحليل والمعالجة...**\n🔄 يتم الآن سحب الملف وتجهيزه للنقل.\n\n▒▒▒▒▒▒▒▒▒▒ 0%", parse_mode="Markdown"
    )

    def universal_archive_process():
        try:
            tmp_dir = "/tmp"
            ydl_opts = {
                'format': 'bestaudio/best[ext=m4a]/bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]/best',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'},
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # تحديث شريط التقدم بصرياً
                asyncio.run_coroutine_threadsafe(query.edit_message_text("⚙️ **جاري التحميل من المصدر...**\n\n███▒▒▒▒▒▒▒ 30%", parse_mode="Markdown"), asyncio.get_event_loop())
                
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
                if os.path.exists(file_path):
                    file_ext = file_path.lower().split('.')[-1]
                    # تحديد النوع: هل هو صوت أم فيديو؟
                    is_audio = file_ext in ['mp3', 'm4a', 'wav', 'ogg', 'flac']
                    
                    method = "sendAudio" if is_audio else "sendVideo"
                    target_chat = MUSIC_STORAGE # إرسال الموسيقى دائماً للقناة الموسيقية
                    
                    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
                    with open(file_path, 'rb') as f:
                        payload = {
                            'chat_id': target_chat, 
                            'caption': f"🎧 {info.get('title')}\n\n✅ تم التحميل بواسطة: @Down2024_bot",
                            'reply_markup': '{"inline_keyboard": [[{"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"}]]}'
                        }
                        files = {'audio' if is_audio else 'video': f}
                        requests.post(send_url, data=payload, files=files)
                    
                    os.remove(file_path)
                    return True, info.get('title'), is_audio
            return False, "لم يتم العثور على محتوى", False
        except Exception as e: return False, str(e), False

    success, title, was_audio = await asyncio.to_thread(universal_archive_process)
    
    if success:
        if was_audio:
            # رسالة مخصصة للموسيقى تخبر المستخدم أين يجد الأغنية
            await status_msg.edit_text(
                f"🏁 **اكتملت أرشفة الأغنية!**\n✅ العنوان: {title}\n\n📍 تم نقل الأغنية إلى **قناة الموسيقى** الخاصة بنا.\nيمكنك الاستماع إليها هناك الآن عبر الزر أدناه 👇",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎧 اذهب للأغنية الآن", url="https://t.me/Musiciqh")]]),
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                f"🏁 **اكتمل أرشفة الفيديو!**\n✅ العنوان: {title}\n📍 تم الحفظ في التخزين العام بنجاح.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📦 تفقد التخزين", url="https://t.me/Musiciqh")]]),
                parse_mode="Markdown"
            )
    else:
        await status_msg.edit_text(f"⚠️ **فشل النظام:** {title}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^arch_"), group=2)
