import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

OWNER_ID = 162459553 
BROADCAST_STATE = 1

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("📢 أرسل رسالة الإذاعة الآن:")
    return BROADCAST_STATE

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    users = bot.active_users
    if not users:
        await update.message.reply_text("❌ القائمة فارغة.")
        return ConversationHandler.END

    status = await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")
    s, f = 0, 0
    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            s += 1
            await asyncio.sleep(0.05)
        except: f += 1
    await status.edit_text(f"✅ اكتملت الإذاعة:\n👤 نجاح: {s}\n❌ فشل: {f}")
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot
    if update.effective_user.id != OWNER_ID: return
    count = len(bot.active_users)
    await update.message.reply_text(f"📊 إحصائيات البوت الحقيقية:\n👥 عدد المستخدمين: {count}")

def setup(app):
    handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, execute_broadcast)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    )
    app.add_handler(handler)
    app.add_handler(CommandHandler("stats", stats_command))
