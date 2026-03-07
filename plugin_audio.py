from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

async def handle_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات أزرار التحميل فقط"""
    query = update.callback_query
    
    # فحص الأمان للسطر 25
    if not query.data or "|" not in query.data:
        return 

    try:
        # فك الحزمة بشكل آمن
        mode, t_id = query.data.split("|")
        url = context.user_data.get(t_id)
        
        if not url:
            await query.answer("⚠️ الرابط لم يعد متوفراً في الذاكرة.")
            return

        await query.answer("⏳ جاري معالجة طلبك...")
        # كود التحميل الفني يستمر هنا...
    except Exception as e:
        print(f"Error in download processing: {e}")

def setup(app):
    app.add_handler(CallbackQueryHandler(handle_downloads))
