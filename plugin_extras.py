from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    msg = (
        "👋 **أهلاً بك في بوت التحميل الذكي**\n\n"
        "📥 أرسل أي رابط فيديو (TikTok, Insta, FB) وسأقوم بتحميله لك.\n"
        "📖 /مساعدة - لعرض التفاصيل"
    )
    if user == 162459553: msg += "\n\n👑 **للمطور:** أرسل `kmr` للوحة التحكم."
    await update.message.reply_text(msg, parse_mode='Markdown')

def setup(app):
    app.add_handler(CommandHandler("start", start_help))
    app.add_handler(CommandHandler("مساعدة", start_help))
