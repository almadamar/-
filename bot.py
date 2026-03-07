import os, importlib
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
DB_FILE = "users.txt"

def register_user(user_id):
    """حفظ المستخدمين في ملف ثابت"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f: pass
    
    with open(DB_FILE, 'r') as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open(DB_FILE, 'a') as f:
            f.write(f"{user_id}\n")

async def track_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل أي مستخدم يرسل رسالة للبوت"""
    if update.effective_user:
        register_user(update.effective_user.id)

async def post_init(application):
    """تحميل جميع الملحقات عند التشغيل"""
    plugins = ['plugin_audio', 'plugin_pro', 'plugin_extras', 'plugin_youtube']
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تم تحميل الملحق: {plugin}")
        except Exception as e:
            print(f"❌ فشل تحميل {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    # إضافة متعقب المستخدمين كأولوية
    app.add_handler(MessageHandler(filters.ALL, track_users), group=-1)
    print("🚀 البوت يعمل الآن بنظام الإدارة المطور...")
    app.run_polling()
