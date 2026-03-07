from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def help_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = update.effective_user.id == 162459553
    text = (
        "📖 **دليل المساعدة:**\n\n"
        "🔹 أرسل أي رابط فيديو للتحميل.\n"
        "🔹 /start - بدء البوت\n"
        "🔹 /مساعدة - عرض الأوامر\n"
    )
    if is_admin:
        text += "\n👑 **للمطور:** أرسل `kmr` للوحة التحكم."
    
    await update.message.reply_text(text, parse_mode='Markdown')

def setup(app):
    app.add_handler(CommandHandler("مساعدة", help_ar))
    app.add_handler(CommandHandler("help", help_ar))
