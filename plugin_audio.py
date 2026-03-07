import os, yt_dlp, asyncio
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

DOWNLOAD_DIR = 'downloads'

async def start_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # حل مشكلة السجل (Log): التأكد من أن الزر يخص التحميل فقط
    if "|" not in query.data: return 

    try:
        mode, t_id = query.data.split("|") # السطر 25 المصلح
        url = context.user_data.get(t_id)
        if not url: return

        await query.answer("⏳ جاري المعالجة...")
        # (باقي كود التحميل الخاص بك هنا)
    except ValueError:
        return # تجاهل أي بيانات لا تطابق الصيغة

def setup(app):
    app.add_handler(CallbackQueryHandler(start_download))
