import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MAIN_CHANNEL = "@Musiciqh" # قناة التخزين
OFFICIAL_CHANNEL = "@UpGo2" # قناتك الرسمية الصحيحة

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    music_sites = ["soundcloud", "spotify", "audiomack", "music.youtube", "apple.com/music"]
    
    if any(p in url.lower() for p in music_sites):
        kb = [
            [InlineKeyboardButton("🌀 أرشفة القائمة كاملة", callback_data=f"list_{url}")],
            [InlineKeyboardButton("🎵 أرشفة أغنية واحدة", callback_data=f"arch_{url}")],
            [
                InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/UpGo2"),
                InlineKeyboardButton("📦 قناة التخزين", url="https://t.me/Musiciqh")
            ]
        ]
        await update.message.reply_text(
            "🎶 **رابط موسيقي مكتشف!**\nسيتم الآن المعالجة بواسطة البوت الخارق 🚀",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data.split("_", 1)[1]
    is_playlist = data.startswith("list_")
    await query.answer()

    # تفعيل حالة "يتم إرسال ملف صوتي" تحت اسم البوت
    try:
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_audio")
    except: pass

    # شريط تحميل تفاعلي مبدئي
    status_msg = await query.edit_message_text(
        "⚙️ **جاري التحميل والأرشفة...**\n🔄 العملية تجري في الخلفية، انتظر قليلاً.\n\n▒▒▒▒▒▒▒▒▒▒ 0%", 
        parse_mode="Markdown"
    )

    def safe_music_process():
        try:
            tmp_dir = "/tmp"
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': not is_playlist,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                entries = info.get('entries', [info]) if is_playlist else [info]
                
                total = len(entries)
                for i, entry in enumerate(entries, 1):
                    # تحديث شريط التقدم بصرياً للمستخدم
                    progress = int((i / total) * 100)
                    bar = "█" * (progress // 10) + "▒" * (10 - (progress // 10))
                    
                    # تحديث الرسالة لتبين حالة التقدم
                    asyncio.run_coroutine_threadsafe(
                        query.edit_message_text(
                            f"⚙️ **جاري المعالجة...**\n🔄 يتم نقل الملفات حالياً.\n\n{bar} {progress}%\n📦 أغنية {i} من {total}",
                            parse_mode="Markdown"
                        ), asyncio.get_event_loop()
                    )

                    file_path = os.path.join(tmp_dir, f"{entry['title']}.mp3")
                    
                    if os.path.exists(file_path):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                        # أزرار التنقل داخل القناة
                        channel_kb = {
                            "inline_keyboard": [[
                                {"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"},
                                {"text": "📢 القناة الرسمية", "url": "https://t.me/UpGo2"}
                            ]]
                        }
                        
                        with open(file_path, 'rb') as audio:
                            payload = {
                                'chat_id': MAIN_CHANNEL, 
                                'caption': f"🎧 {entry['title']}\n\n✅ تم التحميل بواسطة: @Down2024_bot",
                                'reply_markup': str(channel_kb).replace("'", '"')
                            }
                            requests.post(send_url, data=payload, files={'audio': audio})
                        os.remove(file_path)
                    
                    if is_playlist: time.sleep(1) 
                return True, total
        except Exception as e:
            return False, str(e)

    success, result = await asyncio.to_thread(safe_music_process)
    
    if success:
        final_kb = [
            [InlineKeyboardButton("🎧 تفقد قناة التخزين", url="https://t.me/Musiciqh")],
            [InlineKeyboardButton("📢 القناة الرسمية @UpGo2", url="https://t.me/UpGo2")]
        ]
        await status_msg.edit_text(
            f"🏁 **اكتملت الأرشفة بنجاح!**\n✅ تم نقل `{result}` ملفات.\n\n**تم التحميل بواسطة البوت الخارق 🚀**",
            reply_markup=InlineKeyboardMarkup(final_kb),
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text(f"❌ **حدث خطأ:**\n`{result}`")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(arch_|list_)"), group=2)
