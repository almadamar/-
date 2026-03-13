import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MAIN_CHANNEL = "@Musiciqh" 
OFFICIAL_CHANNEL = "@Music_Your_Main_Channel" # قناتك الرسمية

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    music_sites = ["soundcloud", "spotify", "audiomack", "music.youtube", "apple.com/music"]
    
    if any(p in url.lower() for p in music_sites):
        kb = [
            [InlineKeyboardButton("🌀 أرشفة القائمة كاملة", callback_data=f"list_{url}")],
            [InlineKeyboardButton("🎵 أرشفة أغنية واحدة", callback_data=f"arch_{url}")],
            [
                InlineKeyboardButton("📢 القناة الرئيسية", url="https://t.me/Music_Your_Main_Channel"),
                InlineKeyboardButton("📦 قناة التخزين", url=f"https://t.me/{MAIN_CHANNEL.replace('@','')}")
            ]
        ]
        await update.message.reply_text(
            "🎶 **رابط موسيقي مكتشف!**\nاختر نمط الأرشفة المفضل لديك:",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data.split("_", 1)[1]
    is_playlist = data.startswith("list_")
    await query.answer()

    # --- بداية الحالة التفاعلية تحت اسم البوت ---
    # هذه تجعل المستخدم يرى "جاري إرسال ملف صوتي..." بدلاً من كلمة "بوت"
    await context.bot.send_chat_action(chat_id=query.message.chat_id, action=constants.ChatAction.UPLOAD_AUDIO)

    status_msg = await query.edit_message_text(
        "⏳ **جاري العمل في الخلفية...**\n🔄 يتم الآن معالجة الملفات وأرشفتها.\nستظهر النتائج في القناة فوراً ⚡",
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
                
                count = 0
                for entry in entries:
                    count += 1
                    file_path = os.path.join(tmp_dir, f"{entry['title']}.mp3")
                    
                    if os.path.exists(file_path):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                        channel_kb = {
                            "inline_keyboard": [[
                                {"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"},
                                {"text": "📢 القناة الرئيسية", "url": "https://t.me/Music_Your_Main_Channel"}
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
                    
                    if is_playlist: time.sleep(2) 
                return True, count
        except Exception as e:
            return False, str(e)

    success, result = await asyncio.to_thread(safe_music_process)
    
    if success:
        final_kb = [
            [InlineKeyboardButton("🎧 استمع في التخزين", url=f"https://t.me/{MAIN_CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("📢 القناة الرسمية", url="https://t.me/Music_Your_Main_Channel")]
        ]
        await status_msg.edit_text(
            f"🏁 **اكتملت الأرشفة بنجاح!**\n✅ تم نقل `{result}` ملف إلى القناة.\n\n**تم التحميل بواسطة البوت المطور.**",
            reply_markup=InlineKeyboardMarkup(final_kb),
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text(f"❌ **حدث خطأ:**\n`{result}`")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(arch_|list_)"), group=2)
