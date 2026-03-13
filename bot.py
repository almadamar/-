import os
import importlib
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from config_data import TOKEN, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def register_user(user_id):
    db_file = "users.txt"
    if not os.path.exists(db_file):
        open(db_file, 'w').close()
    with open(db_file, 'r') as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(db_file, 'a') as f:
            f.write(f"{user_id}\n")

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        register_user(update.effective_user.id)

async def post_init(application):
    # قائمة الملحقات الشاملة
    plugins = [
        'plugin_monitor',      # 1. المراقبة والتقارير
        'plugin_broadcast',    # 2. الإذاعة الذكية (الجديد)
        'plugin_search',       # 3. البحث في يوتيوب
        'plugin_pro',          # 4. تحميل السوشيال ميديا
        'plugin_youtube',      # 5. تحميل يوتيوب مباشر
        'plugin_extras',       # 6. الأوامر الإضافية
        'plugin_audio_standalone' # 7. محول الصوت
    ]
    
    print("--- 🚀 جاري تشغيل النسخة الاحترافية ---")
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تفعيل: {plugin}")
        except Exception as e:
            print(f"❌ خطأ في {plugin}: {e}")

if __name__ == '__main__':
    # بناء البوت مع JobQueue (ضروري لتقرير الـ 24 ساعة)
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # تتبع كافة المستخدمين (Group -1)
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)

    print("--- ✨ البوت جاهز للعمل بكامل المزايا ---")
    app.run_polling(drop_pending_updates=True)
