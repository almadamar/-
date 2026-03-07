import os, importlib
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
DB_FILE = "users.txt"

def register_user(user_id):
    """تخزين دائم للمستخدمين لمنع النسيان عند التحديث"""
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    with open(DB_FILE, 'r') as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(DB_FILE, 'a') as f:
            f.write(f"{user_id}\n")

async def pre_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل المستخدم في القاعدة قبل تنفيذ أي أمر"""
    if update.effective_user:
        register_user(update.effective_user.id)

async def post_init(application):
    """تحميل الملحقات المنفصلة"""
    plugins = ['plugin_audio', 'plugin_pro', 'plugin_extras']
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
        except Exception as e:
            print(f"❌ Error loading {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.ALL, pre_handler), group=-1)
    print("🚀 البوت متصل ومستعد للعمل...")
    app.run_polling()
