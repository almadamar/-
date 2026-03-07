from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # حل مشكلة السطر 25: إذا لم يوجد "|" يعني أن الزر يخص الإدارة وليس التحميل
    if not query.data or "|" not in query.data:
        return 

    try:
        # الآن التقسيم آمن ولن يسبب خطأ Unpack
        mode, t_id = query.data.split("|")
        url = context.user_data.get(t_id)
        if not url: return
        
        await query.answer("⏳ جاري التحميل...")
        # كود التحميل الخاص بك يكمل هنا
    except Exception:
        return

def setup(app):
    app.add_handler(CallbackQueryHandler(start_download))
