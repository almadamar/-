from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if not await bot.is_subscribed(context.bot, update.effective_user.id):
        await update.message.reply_text("❌ اشترك في القناة أولاً.")
        return
    await update.message.reply_text("🚀 أرسل أي رابط فيديو وسأقوم بتحميله بجودة 720p تلقائياً!")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
