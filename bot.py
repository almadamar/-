import os, importlib, asyncio, datetime, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

# --- 1. إعداد أداة التعقب الذكية (Logging System) ---
logging.basicConfig(
    format='%(asctime)s - 🛠️ [SYSTEM]: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)

DB_FILE = "users_data.txt"

# --- 2. أداة تشخيص استلام الروابط ---
async def diagnostic_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        if "http" in text:
            user = update.effective_user.first_name
            logger.info(f"🔗 رابط مستلم من [{user}]: {text}")
            # هذه الرسالة ستظهر لك في Logs الموقع لتعرف أن البوت استلم الرابط
    return

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

async def post_init(application):
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    
    # تحميل الملحقات مع نظام تقرير الأخطاء
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try:
            module = importlib.import_module(p)
            module.setup(application)
            logger.info(f"✅ الملحق جاهز للعمل: {p}")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل ملف [{p}]: {e}")

    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        logger.info("🚀 نظام الأرشفة (Group 2) متصل الآن.")
    except Exception as e:
        logger.error(f"❌ عطل في نظام الأرشفة: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    # إضافة أداة التشخيص في المجموعة -2 (أعلى مجموعة لمراقبة كل شيء)
    app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), diagnostic_tool), group=-2)
    
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    
    logger.info("⚡ البوت المدمج يعمل.. راقب هذه الشاشة لمعرفة الأخطاء.")
    app.run_polling(drop_pending_updates=True)
