import os, yt_dlp, asyncio, time, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# إعداد الـ Logger الخاص بهذا الموديول
logger = logging.getLogger(__name__)

# --- الإعدادات الخاصة بك ---
ADMIN_ID = 162459553
OLD_CHANNEL_ID = "@UpGo2"         
STORAGE_CHANNEL_ID = "@Musiciqh"   
MAIN_LINK = "https://t.me/UpGo2"
STORAGE_LINK = "https://t.me/Musiciqh"
BOT_USERNAME = "AutoMusicHubBot"

SONG_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320'
    }],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}

async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=OLD_CHANNEL_ID, user_id=user_id)
        return member.status not in ['left', 'kicked']
    except Exception as e:
        logger.warning(f"⚠️ فشل فحص الاشتراك لـ {user_id}: {e}")
        return True # تمرير المستخدم في حال تعطل الفحص

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url or not url.startswith("http"): return

    logger.info(f"📥 [Group 2] استلم رابطاً للأرشفة: {url}")

    if not await check_sub(update, context):
        kb = [[InlineKeyboardButton("📢 اشترك في القناة الأساسية", url=MAIN_LINK)]]
        await update.message.reply_text("⚠️ يرجى الاشتراك أولاً لاستخدام ميزة الأرشفة:", reply_markup=InlineKeyboardMarkup(kb))
        return

    kb = [[InlineKeyboardButton("🚀 بدء التحميل والترحيل لـ Musiciqh", callback_data=f"dl_{url}")]]
    await update.message.reply_text("🔗 نظام الأرشفة جاهز.. اضغط للبدء:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith("dl_"): return
    
    await query.answer()
    url = query.data.replace("dl_", "")
    
    status_msg = await query.edit_message_text("⏳ جاري التحميل والمعالجة... [يرجى الانتظار]")
    logger.info(f"⚡ بدأت عملية التحميل الفعلي للرابط: {url}")

    def download_task():
        try:
            if not os.path.exists('temp'): os.makedirs('temp')
            with yt_dlp.YoutubeDL(SONG_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # التأكد من الامتداد الصحيح بعد المعالجة
                path = filename.rsplit('.', 1)[0] + '.mp3'
                
                logger.info(f"✅ اكتمل التحميل محلياً: {path}")
                
                # إنشاء حلقة أحداث جديدة للرفع داخل الـ thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                with open(path, 'rb') as audio_file:
                    loop.run_until_complete(context.bot.send_audio(
                        chat_id=STORAGE_CHANNEL_ID,
                        audio=audio_file,
                        caption=f"🎧 {info.get('title')}\n✅ تمت الأرشفة عبر @{BOT_USERNAME}"
                    ))
                
                if os.path.exists(path): os.remove(path)
                return True, "Success"
        except Exception as e:
            logger.error(f"❌ خطأ داخل download_task: {str(e)}")
            return False, str(e)

    # تنفيذ التحميل في Thread منفصل لمنع تجميد البوت
    success, error_msg = await asyncio.to_thread(download_task)

    if success:
        kb = [
            [InlineKeyboardButton("📂 مكتبة الأغاني", url=STORAGE_LINK)],
            [InlineKeyboardButton("📢 القناة الأساسية", url=MAIN_LINK)]
        ]
        await status_msg.edit_text("🏁 اكتملت الأرشفة بنجاح في قناة @Musiciqh", reply_markup=InlineKeyboardMarkup(kb))
        logger.info(f"✨ تمت الأرشفة بنجاح للرابط: {url}")
    else:
        await status_msg.edit_text(f"❌ فشل التحميل.\nالسبب: {error_msg}")
        logger.error(f"⚠️ تعثرت الأرشفة للرابط {url} بسبب: {error_msg}")

def setup_music_module(application):
    # استخدام المجموعة 2 ليعمل بالتوازي مع البوت القديم
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click), group=2)
