import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # الكشف عن الروابط الموسيقية (بما فيها قوائم التشغيل)
    if any(p in url.lower() for p in ["soundcloud", "spotify", "playlist", "album", "music.youtube"]):
        kb = [
            [InlineKeyboardButton("🌀 أرشفة القائمة كاملة", callback_data=f"list_{url}")],
            [InlineKeyboardButton("🎵 أرشفة أغنية واحدة فقط", callback_data=f"arch_{url}")],
            [InlineKeyboardButton("📢 قناتنا @Musiciqh", url="https://t.me/Musiciqh")]
        ]
        await update.message.reply_text(
            "📋 **تم رصد رابط (أغنية/قائمة)..**\nإختر نوع الأرشفة التي تريدها:",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data.split("_", 1)[1]
    is_playlist = data.startswith("list_")
    await query.answer()

    # واجهة تفاعلية تشعر المستخدم بالعمل في الخلفية
    status_msg = await query.edit_message_text(
        "⚙️ **جاري فحص الرابط...**\n🔄 العملية تجري في الخلفية، يرجى الانتظار قليلاً.",
        parse_mode="Markdown"
    )

    def process_logic():
        try:
            tmp_dir = "/tmp"
            # إعدادات yt-dlp لدعم القوائم أو الأغاني الفردية
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': not is_playlist, # تفعيل أو تعطيل القوائم
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # إذا كانت قائمة، نمر على العناصر واحداً تلو الآخر
                entries = info.get('entries', [info]) if is_playlist else [info]
                total = len(entries)
                
                count = 0
                for entry in entries:
                    count += 1
                    # تحديث الحالة للمستخدم (تفاعلي) عبر خيط منفصل لضمان عدم التعليق
                    title = entry.get('title', 'Unknown')
                    
                    # تحميل الملف الفعلي
                    ydl.download([entry['webpage_url']])
                    file_path = os.path.join(tmp_dir, f"{title}.mp3")
                    
                    if os.path.exists(file_path):
                        # إرسال الملف للقناة مع زر العودة للبوت
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
                        channel_kb = {"inline_keyboard": [[{"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"}]]}
                        
                        with open(file_path, 'rb') as audio:
                            payload = {
                                'chat_id': '@Musiciqh', 
                                'caption': f"🎧 {title}\n📦 من قائمة: {info.get('title', 'تحميل مباشر')}\n✅ عبر @Down2024_bot",
                                'reply_markup': str(channel_kb).replace("'", '"')
                            }
                            requests.post(send_url, data=payload, files={'audio': audio})
                        
                        os.remove(file_path) # حذف الملف فوراً لتوفير المساحة
                
                return True, total
        except Exception as e:
            return False, str(e)

    # تشغيل المهمة في الخلفية
    success, result = await asyncio.to_thread(process_logic)
    
    if success:
        await status_msg.edit_text(
            f"✅ **اكتملت الأرشفة بنجاح!**\n📦 تم نقل `{result}` أغنية إلى القناة بنجاح.\n\nتفضل بزيارة @Musiciqh",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎧 اذهب للقناة", url="https://t.me/Musiciqh")]]),
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء المعالجة: {result}")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(arch_|list_)"), group=2)
