import os, importlib, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from motor.motor_asyncio import AsyncIOMotorClient
from config_data import TOKEN, MONGO_URI, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# الاتصال السحابي بـ MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client['telegram_bot']
users_col = db['users']

async def register_user(user_id):
    """حفظ المستخدم في السحاب ومنع التكرار"""
    await users_col.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id}},
        upsert=True
    )

async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تتبع كل تفاعل (رسالة أو زر) وحفظه في السحاب"""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id and update.callback_query:
        user_id = update.callback_query.from_user.id
    if user_id:
        await register_user(user_id)

async def post_init(application):
    plugins = [
        'plugin_monitor',      
        'plugin_broadcast',    
        'plugin_search',       
        'plugin_pro',          
        'plugin_youtube',      
        'plugin_extras',       
        'plugin_audio_standalone' 
    ]
    
    print("--- 🚀 تشغيل النسخة الاحترافية السحابية ---")
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ تفعيل: {plugin}")
        except Exception as e:
            print(f"❌ خطأ في {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # الرادار يعمل في الخلفية لكل الحركات (Group -1)
    app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    app.add_handler(CallbackQueryHandler(global_tracker), group=-1)

    print("--- ✨ البوت متصل بالسحاب وجاهز للعمل ببياناتك ---")
    app.run_polling(drop_pending_updates=True)
