import re
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if not await bot.is_subscribed(context.bot, update.effective_user.id):
        await update.message.reply_text("❌ يرجى الاشتراك في القناة أولاً.")
        return
    help_text = "🚀 **كيفية الاستخدام:**\nأرسل أي رابط من (يوتيوب، تيك توك، إنستغرام) وسأقوم بتحميله لك بجودة 720p تلقائياً!"
    await update.message.reply_text(help_text, parse_mode='Markdown')

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
