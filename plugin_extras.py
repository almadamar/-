import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

OWNER_ID = 162459553 
BROADCAST_STATE = 1

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(f"📊 إحصائيات البوت:\n👥 مستخدمين: {len(bot.active_users)}")

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("📢 أرسل رسالة الإذاعة الآن:")
    return BROADCAST_STATE

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    s, f = 0, 0
    msg = await update.message.reply_text("⏳ جاري النشر...")
    for uid in bot.active_users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            s += 1
            await asyncio.sleep(0.05)
        except: f += 1
    await msg.edit_text(f"✅ اكتملت الإذاعة:\n✔ نجاح: {s}\n✖ فشل: {f}")
    return ConversationHandler.END

def setup(app):
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, execute_broadcast)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    ))
