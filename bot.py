import os, importlib, asyncio, datetime, logging
from telegram import Update
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
# هذه الدالة ستحل مشكلة "No error handlers are registered"
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="❌ حدث خطأ فني أثناء المعالجة:", exc_info=context.error)
    # إذا كان هناك تحديث، نحاول إبلاغ المستخدم بوجود مشكلة تقنية
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ عذراً، واجهت مشكلة تقنية أثناء معالجة طلبك. تم تسجيل الخطأ للمراجعة.")
        except: pass

# --- 3. أداة تشخيص استقبال الروابط ---
async def diagnostic_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        if "http" in text:
            user = update.effective_user.first_name if update.effective_user else "Unknown"
            logger.info(f"🔗 [رادار]: استلمت رابطاً من {user} -> {text}")
    return

# --- 4. تسجيل نشاط المستخدمين (الخاص بك) ---
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

# --- 5. نظام التذكير (الخاص بك) ---
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
    # تشغيل التذكير كل يوم
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    
    # تحميل ملحقات البوت القديم
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
    # بناء البوت باستخدام التوكن
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    # إضافة صائد الأخطاء
    app.add_error_handler(error_handler)
    
    # إضافة المجموعات (Groups) بالترتيب الصحيح
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), diagnostic_tool), group=-2)
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    
    logger.info("⚡ البوت المدمج انطلق بنجاح.. راقب الـ Logs الآن.")
    app.run_polling(drop_pending_updates=True)
