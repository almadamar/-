from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "👋 أهلاً بك! أرسل أي رابط للتحميل.\n👑 للمطور: أرسل `kmr` للإدارة."
    await update.message.reply_text(msg)

def setup(app):
    app.add_handler(CommandHandler("start", start_help))
