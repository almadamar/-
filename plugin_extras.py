from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters
from config_data import OWNER_ID, CHANNEL_LINK

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🚀 أرسل أي رابط لتحميله فوراً!\n📢 قناتنا: {CHANNEL_LINK}")

async def kmr_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    with open("users.txt", "r") as f: count = len(f.read().splitlines())
    await update.message.reply_text(f"🛠 لوحة التحكم\n👥 المشتركين: {count}")

def setup(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r'(?i)^kmr$'), kmr_admin))
