import os, yt_dlp, asyncio, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- إعدادات القنوات والروابط الخاصة بك ---
ADMIN_ID = 162459553
OLD_CHANNEL_ID = "@UpGo2"         # القناة الأساسية للاشتراك
STORAGE_CHANNEL_ID = "@Musiciqh"   # قناة التخزين
MAIN_LINK = "https://t.me/UpGo2"
STORAGE_LINK = "https://t.me/Musiciqh"
BOT_USERNAME = "AutoMusicHubBot"

SONG_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'quiet': True,
}

async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=OLD_CHANNEL_ID, user_id=user_id)
        return member.status not in ['left', 'kicked']
    except: return True

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return

    if not await check_sub(update, context):
        kb = [[InlineKeyboardButton("📢 اشترك في القناة الأساسية", url=MAIN_LINK)]]
        await update.message.reply_text("⚠️ يرجى الاشتراك أولاً لاستخدام البوت:", reply_markup=InlineKeyboardMarkup(kb))
        return

    kb = [[InlineKeyboardButton("🚀 بدء التحميل والترحيل", callback_data=f"dl_{url}")]]
    await update.message.reply_text("🔗 تم استلام الرابط.. اضغط للبدء:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("dl_"):
        url = query.data.replace("dl_", "")
        status = await query.edit_message_text("⏳ جاري التحميل... [تحميل 1 ناجح]")
        
        def download_task():
            try:
                if not os.path.exists('temp'): os.makedirs('temp')
                with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=STORAGE_CHANNEL_ID,
                        audio=open(path, 'rb'),
                        caption=f"🎧 {info.get('title')}\n✅ تمت الأرشفة عبر @{BOT_USERNAME}"
                    ))
                    if os.path.exists(path): os.remove(path)
                return True
            except: return False

        if await asyncio.to_thread(download_task):
            kb = [
                [InlineKeyboardButton("📂 مكتبة الأغاني", url=STORAGE_LINK)],
                [InlineKeyboardButton("📢 قناة UpGo2 الأساسية", url=MAIN_LINK)]
            ]
            await status.edit_text("🏁 اكتملت الأرشفة بنجاح!\n\nيمكنك الوصول لخدماتنا عبر الأزرار أدناه:", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await status.edit_text("❌ فشل التحميل، جرب رابطاً آخر.")

def setup_music_module(application):
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received))
    application.add_handler(CallbackQueryHandler(on_button_click))
