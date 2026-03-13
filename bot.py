import os, importlib, asyncio, datetime, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    ApplicationHandlerStop 
)
# تأكد من تطابق هذه المسميات مع ملف config_data.py الخاص بك
from config_data import TOKEN, SECOND_TOKEN, REQUIRED_CHANNEL_ID, CHANNEL_LINK, OWNER_ID, DOWNLOAD_DIR

# --- 1. إعداد نظام المراقبة ---
logging.basicConfig(
    format='%(asctime)s - 🛠️ [%(levelname)s]: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)

DB_FILE = "users_data.txt"

# --- 2. دالة التحقق من الاشتراك الإجباري (المنقحة) ---
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return True
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True

    try:
        # فحص العضوية في القناة الرسمية
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.warning(f"⚠️ خطأ في فحص الاشتراك (تأكد أن البوت أدمن): {e}")
        # في حال وجود خطأ في الصلاحيات، نسمح بالمرور مؤقتاً لضمان عدم توقف الخدمة
        return True 

    kb = [[InlineKeyboardButton("📢 اشترك في القناة الرسمية", url=CHANNEL_LINK)]]
    await update.message.reply_text(
        "⚠️ **عذراً عزيزي، يجب عليك الاشتراك في قناة المنظومة الرسمية أولاً لتتمكن من استخدام البوتات.**",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    return False

# --- 3. دالة التوجيه الذكي (لمنع التداخل) ---
async def redirect_to_archiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    url = update.message.text.lower()
    target_sites = ["soundcloud.com", "pinterest.com", "pin.it", "snapchat.com", ".mp3", "spotify.com", "apple.com", "music.youtube"]
    
    if any(site in url for site in target_sites):
        if update.effective_chat.type in ['group', 'supergroup']:
            user_name = update.effective_user.first_name if update.effective_user else "عزيزي"
            text = f"👋 أهلاً {user_name}!\n\nهذه الروابط يتم معالجتها حصراً عبر بوت الأرشفة الخاص بنا 📥✨"
            keyboard = [[InlineKeyboardButton("🚀 اذهب إلى بوت الأرشفة", url="https://t.me/AutoMusicHubBot")]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            raise ApplicationHandlerStop 

# --- 4. نظام التذكير وتتبع النشاط ---
async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        with open(DB_FILE, "a") as f: f.write(f"{user_id}|{now}\n")

async def reminder_task(context: ContextTypes.DEFAULT_TYPE):
    # كود التذكير الخاص بك (يبقى كما هو)
    pass

# --- 5. تهيئة الملحقات والمحركات ---
async def post_init_bot1(application):
    # إضافة فحص الاشتراك للبوت الأول في المجموعة -3
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_subscription), group=-3)
    
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try:
            module = importlib.import_module(p)
            module.setup(application)
            logger.info(f"✅ تم تفعيل الملحق: {p}")
        except Exception as e: logger.error(f"❌ خطأ {p}: {e}")

async def post_init_bot2(application):
    # إضافة فحص الاشتراك للبوت الثاني أيضاً
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_subscription), group=-3)
    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        logger.info("🚀 نظام الأرشفة جاهز.")
    except Exception as e: logger.error(f"❌ خطأ موديول الموسيقى: {e}")

# --- 6. المحرك المزدوج الحقيقي (Dual-Core Engine) ---
async def main():
    # بناء البوت الأول
    bot1_app = ApplicationBuilder().token(TOKEN).post_init(post_init_bot1).build()
    # بناء البوت الثاني
    bot2_app = ApplicationBuilder().token(SECOND_TOKEN).post_init(post_init_bot2).build()

    # إضافة المعالجات الإضافية للبوت الأساسي
    bot1_app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), redirect_to_archiver), group=0)
    bot1_app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)

    logger.info("⚡ جاري تشغيل البوتين معاً بشكل متوازي...")
    
    # السطر السحري لتشغيل البوتين دون توقف
    await asyncio.gather(
        bot1_app.run_polling(drop_pending_updates=True, close_loop=False),
        bot2_app.run_polling(drop_pending_updates=True, close_loop=False)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⚠️ تم إيقاف المنظومة.")
