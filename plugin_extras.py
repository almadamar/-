import asyncio
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

OWNER_ID = 162459553 
BROADCAST_STATE = 1

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("📢 أرسل الرسالة التي تريد إذاعتها (نص/ميديا):")
    return BROADCAST_STATE

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot # استيراد حي لجلب قائمة اليوزرات الحالية
    users = bot.active_users
    
    if not users:
        await update.message.reply_text("❌ القائمة فارغة حالياً.")
        return ConversationHandler.END

    m = await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(users)} مستخدم...")
    s, f = 0, 0
    
    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
            s += 1
            await asyncio.sleep(0.05)
        except: f += 1
            
    await m.edit_text(f"✅ اكتملت الإذاعة:\n👤 نجاح: {s}\n❌ فشل: {f}")
    return ConversationHandler.END

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import bot # استيراد حي للقائمة
    if update.effective_user.id != OWNER_ID: return
    
    # حساب المستخدمين المسجلين في الجلسة الحالية
    count = len(bot.active_users)
    await update.message.reply_text(f"📊 **إحصائيات البوت الحالية:**\n👥 عدد المستخدمين النشطين: {count}")

def setup(app):
    handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, execute_broadcast)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    )
    app.add_handler(handler)
    app.add_handler(CommandHandler("stats", stats_command))
