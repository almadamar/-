import os, importlib, asyncio, datetime, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# استيراد الإعدادات
from config_data import TOKEN, SECOND_TOKEN, REQUIRED_CHANNEL_ID, CHANNEL_LINK, OWNER_ID, DOWNLOAD_DIR

logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# مجلد التحميلات
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# --- 1. التحقق من الاشتراك ---
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return True
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']: return True
    except: return True # تمرير في حال الخطأ لضمان العمل
    
    kb = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)]]
    await update.message.reply_text("⚠️ يجب الاشتراك أولاً للاستخدام.", reply_markup=InlineKeyboardMarkup(kb))
    return False

# --- 2. محرك البوت الأساسي ---
async def post_init(application):
    # تحميل الملحقات القديمة (انستا، تيك توك، الخ)
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try:
            module = importlib.import_module(p)
            module.setup(application)
            logger.info(f"✅ تم تفعيل: {p}")
        except Exception as e: logger.error(f"❌ خطأ {p}: {e}")

    # تفعيل موديول الأرشفة داخل نفس البوت لضمان عدم توقف الـ Loop
    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        logger.info("🚀 نظام الأرشفة مدمج الآن.")
    except Exception as e: logger.error(f"❌ خطأ موديول الموسيقى: {e}")

# --- 3. التشغيل الآمن (Single Application) ---
if __name__ == '__main__':
    # سنقوم بتشغيل البوت الأساسي فقط، ونربط مهام البوت الثاني به
    # لتجنب خطأ RuntimeError: This event loop is already running
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    # إضافة التحقق من الاشتراك كأولوية
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_subscription), group=-3)
    
    logger.info("⚡ البوت الأساسي يعمل الآن (نظام الدمج الآمن).")
    app.run_polling(drop_pending_updates=True)
