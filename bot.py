import os
import importlib
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from config_data import TOKEN, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def register_user(user_id):
    """حفظ الآيدي في ملف users.txt إذا لم يكن موجوداً"""
    db_file = "users.txt"
    if not os.path.exists(db_file):
        open(db_file, 'w').close()
    
    with open(db_file, 'r') as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open(db_file, 'a') as f:
            f.write(f"{user_id}\n")
        print(f"👤 مستخدم جديد تم تسجيله: {user_id}")

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تتبع شامل: رسائل، أزرار، أو أي تفاعل"""
    user_id = None
    if update.effective_user:
        user_id = update.effective_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id

    if user_id:
        register_user(user_id)

async def post_init(application):
    plugins = [
        'plugin_monitor',      # المراقبة
        'plugin_broadcast',    # الإذاعة
        'plugin_search',       # البحث
        'plugin_pro',          # تحميل سوشيال
        'plugin_youtube',      # تحميل يوتيوب
        'plugin_extras',       # أوامر إضافية
        'plugin_audio_standalone' # محول صوت
    ]
    
    print("--- 🚀 تشغيل النسخة الاحترافية (تتبع شامل) ---")
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تفعيل: {plugin}")
        except Exception as e:
            print(f"❌ خطأ في {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # التتبع يعمل في الخلفية (Group -1) لكل التحديثات
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)

    print("--- ✨ البوت يسجل الآن كل من يتفاعل معه ---")
    app.run_polling(drop_pending_updates=True)
