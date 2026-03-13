import os, importlib, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from motor.motor_asyncio import AsyncIOMotorClient
from config_data import TOKEN, MONGO_URI, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# اتصال مباشر وسريع مع تجاوز مشاكل SSL handshake في Render
client = AsyncIOMotorClient(
    MONGO_URI, 
    tlsAllowInvalidCertificates=True, # حل نهائي لمشكلة SSL
    serverSelectionTimeoutMS=5000     # تقليل وقت الانتظار لتسريع البوت
)
db = client['telegram_bot']
users_col = db['users']

async def register_user(user_id):
    """حفظ صامت وسريع في السحاب"""
    try:
        await users_col.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id}},
            upsert=True
        )
    except:
        pass # تجاهل الخطأ لضمان عدم تأثر سرعة التحميل

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id and update.callback_query:
        user_id = update.callback_query.from_user.id
    if user_id:
        asyncio.create_task(register_user(user_id)) # تشغيل في الخلفية لضمان السرعة

async def post_init(application):
    # تم إزالة 'plugin_audio_standalone' بناءً على طلبك للاكتفاء بالمدمج
    plugins = [
        'plugin_monitor', 'plugin_broadcast', 'plugin_search', 
        'plugin_pro', 'plugin_youtube', 'plugin_extras'
    ]
    print("--- 🚀 تشغيل النسخة السحابية السريعة ---")
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
