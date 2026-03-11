import os
import importlib
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from config_data import TOKEN, DOWNLOAD_DIR

# التأكد من وجود مجلد التحميلات عند بدء التشغيل
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def register_user(user_id):
    """تسجيل المستخدمين في قاعدة بيانات نصية بسيطة"""
    db_file = "users.txt"
    if not os.path.exists(db_file):
        open(db_file, 'w').close()
    with open(db_file, 'r') as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(db_file, 'a') as f:
            f.write(f"{user_id}\n")

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تتبع المستخدمين الجدد قبل معالجة أي طلب"""
    if update.effective_user:
        register_user(update.effective_user.id)

async def post_init(application):
    """تحميل الملحقات ديناميكياً عند بدء البوت"""
    # ترتيب الملحقات (تمت إضافة الملحق المستقل الجديد للصوت)
    plugins = [
        'plugin_pro', 
        'plugin_youtube', 
        'plugin_extras', 
        'plugin_audio_standalone'
    ]
    
    print("--- 🚀 جاري تشغيل محرك البوت ---")
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تم تفعيل الملحق: {plugin}")
        except Exception as e:
            print(f"❌ خطأ في تحميل الملحق {plugin}: {e}")

if __name__ == '__main__':
    # بناء تطبيق البوت مع تحسينات الأداء
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # إضافة متعقب المستخدمين في مجموعة منفصلة (Group -1) ليعمل مع كل الرسائل
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)

    print("--- ✨ البوت يعمل الآن بأقصى سرعة واستجابة ---")
    
    # بدء استقبال الرسائل
    app.run_polling(drop_pending_updates=True)
