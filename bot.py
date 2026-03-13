import os, importlib, asyncio, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

# ملف تخزين البيانات: آيدي المستخدم | تاريخ آخر تفاعل
DB_FILE = "users_data.txt"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def update_user_activity(user_id):
    """تحديث تاريخ آخر تفاعل للمستخدم"""
    user_id = str(user_id)
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    data = {}
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if "|" in line:
                    uid, d = line.strip().split("|")
                    data[uid] = d
    
    data[user_id] = now
    with open(DB_FILE, "w") as f:
        for uid, d in data.items():
            f.write(f"{uid}|{d}\n")

async def reminder_task(context: ContextTypes.DEFAULT_TYPE):
    """مهمة التذكير التلقائي: تعمل كل 24 ساعة"""
    if not os.path.exists(DB_FILE):
        return

    now = datetime.datetime.now()
    with open(DB_FILE, "r") as f:
        lines = f.readlines()

    for line in lines:
        try:
            uid, last_date_str = line.strip().split("|")
            last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d")
            diff = (now - last_date).days

            # إذا مر 3 أيام بالضبط على آخر تحميل
            if diff == 5:
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text="مرحباً! ماذا تفكر اليوم بالتحميل؟ أنا أنتظر روابط منك 📥✨"
                    )
                except:
                    pass # تخطي إذا قام المستخدم بحظر البوت
        except:
            continue

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id and update.callback_query:
        user_id = update.callback_query.from_user.id
    if user_id:
        update_user_activity(user_id)

async def post_init(application):
    # تشغيل نظام التذكير ليفحص مرة كل يوم (86400 ثانية)
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
        except: pass

if __name__ == '__main__':
    # ملاحظة: يجب أن يحتوي التوكن على JobQueue (موجود تلقائياً في المكتبة)
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    app.run_polling(drop_pending_updates=True)
