import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MAIN_CHANNEL = "@Musiciqh" 
OFFICIAL_CHANNEL = "@UpGo2"

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
            "🎶 **رابط موسيقي مكتشف!**\nسيتم المعالجة الآن عبر نظام الأرشفة الذكي 🚀",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data.split("_", 1)[1]
    is_playlist = data.startswith("list_")
    await query.answer()

    # شريط تحميل تفاعلي مع نقاط متحركة
    status_msg = await query.edit_message_text(
        "⚙️ **جاري فحص وتجاوز الحماية...**\n🔄 يتم التحميل في الخلفية بواسطة البوت.\n\n▒▒▒▒▒▒▒▒▒▒ 0%", 
        parse_mode="Markdown"
    )

    def safe_music_process():
        try:
            tmp_dir = "/tmp"
            # إعدادات متقدمة لتجاوز خطأ 403 Forbidden الظاهر في السجلات
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': not is_playlist,
                # تمويه متطور لمحاكاة متصفح حقيقي
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                },
                'geo_bypass': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # محاولة الحصول على المعلومات مع تجاوز الحظر
                info = ydl.extract_info(url, download=True)
                entries = info.get('entries', [info]) if is_playlist else [info]
                
                total = len(entries)
                for i, entry in enumerate(entries, 1):
                    # تحديث شريط التقدم التفاعلي
                    progress = int((i / total) * 100)
                    bar = "█" * (progress // 10) + "▒" * (10 - (progress // 10))
                    
                    asyncio.run_coroutine_threadsafe(
                        query.edit_message_text(
                            f"⚙️ **جاري النقل للأرشيف...**\n\n{bar} {progress}%\n📦 أغنية {i} من {total}\n✅ تم التحميل بواسطة البوت",
                            parse_mode="Markdown"
                        ), asyncio.get_event_loop()
                    )

                    file_path = os.path.join(tmp_dir, f"{entry['title']}.mp3")
                    
                    if os.path.exists(file_path):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                        channel_kb = {
                            "inline_keyboard": [[
                                {"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"},
                                {"text": "📢 القناة الرسمية", "url": "https://t.me/UpGo2"}
                            ]]
                        }
                        
                        with open(file_path, 'rb') as audio:
                            payload = {
                                'chat_id': MAIN_CHANNEL, 
                                'caption': f"🎧 {entry.get('title', 'Music')}\n\n✅ تم التحميل بواسطة: @Down2024_bot",
                                'reply_markup': str(channel_kb).replace("'", '"')
                            }
                            requests.post(send_url, data=payload, files={'audio': audio})
                        os.remove(file_path)
                    
                    if is_playlist: time.sleep(2) # تأخير لتفادي حظر الآي بي
                return True, total
        except Exception as e:
            return False, str(e)

    success, result = await asyncio.to_thread(safe_music_process)
    
    if success:
        final_kb = [[InlineKeyboardButton("🎧 قناة التخزين", url="https://t.me/Musiciqh")],
                    [InlineKeyboardButton("📢 القناة الرسمية @UpGo2", url="https://t.me/UpGo2")]]
        await status_msg.edit_text(
            f"🏁 **اكتملت المهمة بنجاح!**\n📦 تم أرشفة `{result}` ملفات.\n\n**تم التحميل بواسطة البوت الخارق 🚀**",
            reply_markup=InlineKeyboardMarkup(final_kb), parse_mode="Markdown"
        )
    else:
        # رسالة الخطأ أصبحت تشرح السبب (مثل حظر 403)
        await status_msg.edit_text(f"❌ **توقف النظام مؤقتاً:**\nالموقع قام بحظر الطلب (403). يرجى المحاولة لاحقاً.")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(arch_|list_)"), group=2)
