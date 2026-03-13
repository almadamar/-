import os, importlib, asyncio, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

DB_FILE = "users_data.txt"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# --- نظام التذكير (كودك المستقر) ---
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

async def post_init(application):
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    # تحميل إضافات القديم
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try: module = importlib.import_module(p); module.setup(application)
        except: pass
    # دمج نظام الأرشفة (الجديد)
    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        print("✅ تم دمج البوتين بنجاح!")
    except Exception as e: print(f"❌ خطأ دمج الجديد: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    app.run_polling(drop_pending_updates=True)
