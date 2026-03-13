import os, importlib, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ملف تخزين المشتركين المحلي
USERS_FILE = "users.txt"

def register_user_local(user_id):
    """حفظ المستخدم في ملف نصي بسيط"""
    user_id = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write(user_id + "\n")
        return

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    
    if user_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(user_id + "\n")

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id and update.callback_query:
        user_id = update.callback_query.from_user.id
    if user_id:
        register_user_local(user_id)

async def post_init(application):
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    print("--- 🚀 تشغيل البوت بنظام التخزين المحلي (مستقر) ---")
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تفعيل: {plugin}")
        except Exception as e:
            print(f"❌ خطأ في {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)
    app.run_polling(drop_pending_updates=True)
