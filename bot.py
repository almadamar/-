import os, importlib, asyncio, datetime, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

# --- 1. إعداد نظام المراقبة والتعقب (Logging) ---
logging.basicConfig(
    format='%(asctime)s - 🛠️ [%(levelname)s]: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)

DB_FILE = "users_data.txt"

# --- 2. صائد الأخطاء الشامل (Error Handler) ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="❌ حدث خطأ فني أثناء المعالجة:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ عذراً، واجهت مشكلة تقنية أثناء معالجة طلبك. تم تسجيل الخطأ للمراجعة.")
        except: pass

# --- 3. دالة التوجيه الذكي للمجموعات (الميزة الجديدة) ---
async def redirect_to_archiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تعمل فقط في المجموعات لتوجيه المستخدم لبوت الأرشفة المختص
    if update.effective_chat.type in ['group', 'supergroup'] and update.message and update.message.text:
        url = update.message.text.lower()
        # المنصات التي نريد تحويلها للبوت الثاني
        target_sites = ["soundcloud.com", "pinterest.com", "pin.it", "snapchat.com", ".mp3"]
        
        if any(site in url for site in target_sites):
            user_name = update.effective_user.first_name if update.effective_user else "يا صديقي"
            text = (
                f"👋 أهلاً {user_name}!\n\n"
                f"لقد رصدت رابطاً (صوتيات/أرشفة)..\n"
                f"هذه الروابط يتم تحميلها وتغيير حقوقها حصراً عبر بوت الأرشفة الخاص بنا 📥✨"
            )
            # زر التحويل للبوت الثاني @AutoMusicHubBot
            keyboard = [[InlineKeyboardButton("🚀 اذهب إلى بوت الأرشفة", url="https://t.me/AutoMusicHubBot")]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --- 4. أداة تشخيص استقبال الروابط ---
async def diagnostic_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        if "http" in text:
            user = update.effective_user.first_name if update.effective_user else "Unknown"
            logger.info(f"🔗 [رادار]: استلمت رابطاً من {user} -> {text}")
    return

# --- 5. تسجيل نشاط المستخدمين ونظام التذكير ---
async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else (update.callback_query.from_user.id if update.callback_query else None)
    if user_id:
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        data = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                for l in f:
                    if "|" in l: uid, d = l.strip().split("|"); data[uid] = d
        data[str(user_id)] = now
        with open(DB_FILE, "w") as f:
            for uid, d in data.items(): f.write(f"{uid}|{d}\n")

async def reminder_task(context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DB_FILE): return
    now = datetime.datetime.now()
    with open(DB_FILE, "r") as f: lines = f.readlines()
    for line in lines:
        try:
            uid, last_date_str = line.strip().split("|")
            if (now - datetime.datetime.strptime(last_date_str, "%Y-%m-%d")).days == 5:
                try: await context.bot.send_message(chat_id=int(uid), text="مرحباً! ماذا تفكر اليوم بالتحميل؟ 📥✨")
                except: pass
        except: continue

# --- 6. دالة بدء التشغيل ودمج الملحقات ---
async def post_init(application):
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    
    # تحميل ملحقات البوت القديم (انستا، تيك توك، فيس، يوتيوب، الخ)
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try:
            module = importlib.import_module(p)
            module.setup(application)
            logger.info(f"✅ تم تفعيل الملحق: {p}")
        except Exception as e:
            logger.error(f"❌ فشل تحميل الملف [{p}]: {e}")

    # تحميل نظام الأرشفة الجديد
    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        logger.info("🚀 نظام الأرشفة (Auto Music Hub) يعمل الآن بالتوازي.")
    except Exception as e:
        logger.error(f"❌ فشل دمج موديول الأرشفة الجديد: {e}")

# --- 7. نقطة الانطلاق الأساسية ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    # إضافة صائد الأخطاء
    app.add_error_handler(error_handler)
    
    # المجموعة 0: دالة التوجيه للمجموعات (تعمل أولاً للروابط المحددة)
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), redirect_to_archiver), group=0)
    
    # المجموعة -2: التشخيص
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), diagnostic_tool), group=-2)
    
    # المجموعة -1: تتبع المستخدمين
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    
    logger.info("⚡ البوت المدمج انطلق بنجاح مع نظام التوجيه الذكي..")
    app.run_polling(drop_pending_updates=True)
