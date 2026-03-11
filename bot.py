import os, importlib, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
DB_FILE = "users.txt"
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

def register_user(user_id):
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    with open(DB_FILE, 'r') as f: users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, 'a') as f: f.write(f"{user_id}\n")

async def track_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        register_user(update.effective_user.id)

async def post_init(application):
    plugins = ['plugin_pro', 'plugin_youtube', 'plugin_audio', 'plugin_extras']
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ Active: {plugin}")
        except Exception as e:
            print(f"❌ Error {plugin}: {e}")

if __name__ == '__main__':
    # استخدام تقنيات الـ Async لتحسين الاستجابة
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, track_and_save), group=-1)
    print("--- BOT IS RUNNING FAST ---")
    app.run_polling()
