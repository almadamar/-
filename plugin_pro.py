import asyncio
import re
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if not await bot.is_subscribed(context.bot, update.effective_user.id):
        await update.message.reply_text("❌ اشترك في القناة أولاً.")
        return
    help_text = (
        "🚀 **دليل خدمات البوت الشامل** 🚀\n\n"
        "🎬 **تيك توك:** بدون علامة مائية.\n"
        "📸 **إنستغرام:** ريلز، قصص، وألبومات.\n"
        "📺 **يوتيوب:** فيديو 720p أو صوت MP3.\n"
        "💡 أرسل أي رابط مباشرة وسأقوم بمعالجته فوراً!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def auto_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if not await bot.is_subscribed(context.bot, update.effective_user.id): return
    text = update.message.text
    if "tiktok.com" in text: await update.message.reply_text("🎬 تم التعرف على تيك توك.. جاري السحب.")
    elif "instagram.com" in text: await update.message.reply_text("📸 تم التعرف على إنستغرام.. جاري المعالجة.")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(re.compile(r'tiktok|instagram', re.IGNORECASE)), auto_info), group=-1)
