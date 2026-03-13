import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from config_data import OWNER_ID

# تعريف حالات المحادثة
AWAITING_TEXT, CONFIRM_BROADCAST = range(2)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المرحلة الأولى: طلب النص من المدير"""
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END

    await update.message.reply_text("📥 **نظام الإذاعة المطور**\n\nيرجى كتابة الرسالة التي تريد نشرها لجميع المستخدمين الآن:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المرحلة الثانية: معاينة الرسالة وعرض الأزرار"""
    context.user_data['broadcast_msg'] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("✅ نشر للجميع", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_send")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 **معاينة الرسالة:**\n\n{update.message.text}\n\n**هل تريد نشرها الآن؟**",
        reply_markup=reply_markup
    )
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المرحلة الثالثة: التنفيذ والحذف بعد الانتهاء"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم إلغاء عملية الإذاعة.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    db_file = "users.txt"
    
    if not os.path.exists(db_file):
        await query.edit_message_text("❌ لا يوجد مستخدمون مسجلون.")
        return ConversationHandler.END

    with open(db_file, "r") as f:
        user_ids = list(set(f.read().splitlines())) # إزالة التكرار

    await query.edit_message_text(f"🚀 جاري النشر إلى {len(user_ids)} مستخدم...")
    
    sent, fail = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.05) # حماية من حظر تليجرام
        except:
            fail += 1

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"✅ **اكتملت الإذاعة بنجاح**\n\n🟢 تم الإرسال: {sent}\n🔴 حظروا البوت: {fail}"
    )
    return ConversationHandler.END

def setup(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            AWAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            CONFIRM_BROADCAST: [CallbackQueryHandler(execute_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    app.add_handler(conv_handler)
