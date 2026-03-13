import os, yt_dlp, asyncio, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- إعدادات القنوات والروابط ---
ADMIN_ID = 162459553
OLD_CHANNEL_ID = "@UpGo2"  # القناة الأساسية
STORAGE_CHANNEL_ID = "@Musiciqh" # قناة التخزين
MAIN_CHANNEL_LINK = "https://t.me/UpGo2"
STORAGE_LINK = "https://t.me/Musiciqh"
OLD_BOT_LINK = "https://t.me/ubgo3_bot" # ضع هنا معرف بوت التحميل القديم إذا كان مختلفاً

SONG_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
    'outtmpl': 'temp/track_%(title)s.%(ext)s',
    'quiet': True,
}

async def check_user_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=OLD_CHANNEL_ID, user_id=user_id)
        if member.status in ['left', 'kicked']: return False
        return True
    except: return True 

async def handle_incoming_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return

    if not await check_user_sub(update, context):
        kb = [[InlineKeyboardButton("📢 اشترك في قناتنا الأساسية", url=MAIN_CHANNEL_LINK)]]
        await update.message.reply_text(
            "⚠️ عذراً! يجب الاشتراك في القناة الأساسية لاستخدام البوت:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    kb = [[InlineKeyboardButton("🚀 بدء التحميل والترحيل", callback_data=f"start_dl_{url}")]]
    await update.message.reply_text("✅ الرابط جاهز.. ابدأ الأرشفة الآن:", reply_markup=InlineKeyboardMarkup(kb))

async def process_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("start_dl_"):
        url = query.data.replace("start_dl_", "")
        status_msg = await query.edit_message_text("⏳ جاري المعالجة... [تحميل 1 ناجح]")
        
        def run_dl():
            try:
                with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=STORAGE_CHANNEL_ID,
                        audio=open(path, 'rb'),
                        caption=f"🎧 {info.get('title')}\n✅ تمت الأرشفة عبر @{context.bot.username}"
                    ))
                    if os.path.exists(path): os.remove(path)
                return True
            except: return False

        success = await asyncio.to_thread(run_dl)
        
        if success:
            # --- قسم أزرار كافة الخدمات والقنوات ---
            kb = [
                [InlineKeyboardButton("📂 مكتبة الأغاني (التخزين)", url=STORAGE_LINK)],
                [InlineKeyboardButton("🤖 بوت تحميل الفيديوهات (القديم)", url=OLD_BOT_LINK)],
                [InlineKeyboardButton("📢 قناتنا الأساسية (UpGo2)", url=MAIN_CHANNEL_LINK)]
            ]
            await status_msg.edit_text(
                "🏁 اكتمل التحميل والترحيل بنجاح!\n\n🌟 **كافة خدماتنا وروابطنا:**\nيمكنك الوصول لجميع بوتاتنا وقنواتنا من خلال الأزرار أدناه:",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        else:
            await status_msg.edit_text("❌ فشل التحميل، يرجى المحاولة لاحقاً.")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), handle_incoming_link))
    application.add_handler(CallbackQueryHandler(process_button))
