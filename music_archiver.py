import os, yt_dlp, asyncio, requests, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# البيانات الأساسية
BOT_TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
MAIN_CHANNEL = "@Musiciqh" 
OFFICIAL_CHANNEL = "@UpGo2"

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text
    
    # قائمة المواقع المدعومة (أغاني وفيديوهات)
    is_music = any(p in url.lower() for p in ["soundcloud", "spotify", "audiomack", "music.youtube"])
    is_video = any(p in url.lower() for p in ["instagram", "tiktok", "facebook", "pin.it", "youtube.com/watch"])

    if is_music or is_video:
        type_label = "🎵 موسيقي" if is_music else "🎬 فيديو"
        kb = [
            [InlineKeyboardButton(f"🌀 أرشفة كاملة ({type_label})", callback_data=f"list_{url}")],
            [InlineKeyboardButton("📢 القناة الرسمية", url=f"https://t.me/{OFFICIAL_CHANNEL[1:]}"),
             InlineKeyboardButton("📦 التخزين", url=f"https://t.me/{MAIN_CHANNEL[1:]}")]
        ]
        await update.message.reply_text(
            f"✅ **تم رصد رابط {type_label}**\nسيتم التحميل الآن عبر النظام التفاعلي المطور 🚀",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    url = data.split("_", 1)[1]
    is_playlist = data.startswith("list_")
    await query.answer()

    # --- 1. تفعيل الحالة التفاعلية تحت الاسم (العلامة الخضراء) ---
    # ستظهر للمستخدم "يتم إرسال ملف..." بدلاً من كلمة "بوت"
    try:
        action = "upload_audio" if "music" in url or "sound" in url else "upload_video"
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=action)
    except: pass

    # --- 2. رسالة الحالة مع شريط التقدم التفاعلي ---
    status_msg = await query.edit_message_text(
        "⚙️ **جاري فحص وتجاوز الحماية...**\n🔄 العملية تجري في الخلفية بواسطة البوت.\n\n▒▒▒▒▒▒▒▒▒▒ 0%", 
        parse_mode="Markdown"
    )

    def process_with_anti_block():
        try:
            tmp_dir = "/tmp"
            # إعدادات متقدمة جداً لتجاوز خطأ 403 Forbidden
            ydl_opts = {
                'format': 'bestaudio/best' if "music" in url or "sound" in url else 'best',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'noplaylist': not is_playlist,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Referer': 'https://www.google.com/',
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                entries = info.get('entries', [info]) if is_playlist else [info]
                
                total = len(entries)
                for i, entry in enumerate(entries, 1):
                    # --- 3. تحديث شريط التقدم المرئي ---
                    progress = int((i / total) * 100)
                    bar = "█" * (progress // 10) + "▒" * (10 - (progress // 10))
                    
                    asyncio.run_coroutine_threadsafe(
                        query.edit_message_text(
                            f"⚙️ **جاري الأرشفة والرفع...**\n\n{bar} {progress}%\n📦 معالجة: {i} من {total}\n✅ تم التحميل بواسطة البوت",
                            parse_mode="Markdown"
                        ), asyncio.get_event_loop()
                    )

                    file_path = ydl.prepare_filename(entry)
                    if os.path.exists(file_path):
                        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                        channel_kb = {"inline_keyboard": [[
                            {"text": "🤖 العودة للبوت", "url": "https://t.me/Down2024_bot"},
                            {"text": "📢 القناة الرسمية", "url": f"https://t.me/{OFFICIAL_CHANNEL[1:]}"}
                        ]]}
                        
                        with open(file_path, 'rb') as f:
                            payload = {
                                'chat_id': MAIN_CHANNEL, 
                                'caption': f"🎧 {entry.get('title', 'تحميل جديد')}\n\n✅ تم التحميل بواسطة: @Down2024_bot",
                                'reply_markup': str(channel_kb).replace("'", '"')
                            }
                            requests.post(send_url, data=payload, files={'document': f})
                        os.remove(file_path)
                    
                    if is_playlist: time.sleep(1.5)
                return True, total
        except Exception as e:
            return False, str(e)

    success, result = await asyncio.to_thread(process_with_anti_block)
    
    if success:
        final_kb = [[InlineKeyboardButton("🎧 قناة التخزين", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
                    [InlineKeyboardButton(f"📢 القناة الرسمية {OFFICIAL_CHANNEL}", url=f"https://t.me/{OFFICIAL_CHANNEL[1:]}")]]
        await status_msg.edit_text(
            f"🏁 **اكتملت جميع التحميلات!**\n📦 تم أرشفة `{result}` ملفات بنجاح.\n\n**تم التحميل بواسطة البوت الخارق 🚀**",
            reply_markup=InlineKeyboardMarkup(final_kb), parse_mode="Markdown"
        )
    else:
        # حل مشكلة 403
        await status_msg.edit_text(f"⚠️ **تنبيه من النظام:**\nالموقع رفض الطلب (403). حاول مجدداً مع رابط آخر أو بعد قليل.")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click, pattern="^(arch_|list_)"), group=2)
