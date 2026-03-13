import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from config_data import OWNER_ID

AWAITING_TEXT, CONFIRM_BROADCAST = range(2)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END
    await update.message.reply_text("📥 **نظام الإذاعة الشامل**\n\nاكتب الآن الرسالة التي تريد إرسالها لكل من دخل البوت:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    keyboard = [[InlineKeyboardButton("✅ تأكيد النشر للجميع", callback_data="confirm_send")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_send")]]
    await update.message.reply_text(
        f"📝 **معاينة:**\n\n{update.message.text}\n\n**هل أنت متأكد من النشر؟**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    db_file = "users.txt"
    
    if not os.path.exists(db_file) or os.path.getsize(db_file) == 0:
        await query.edit_message_text("❌ لم يتم العثور على أي مستخدمين مسجلين في النظام بعد.")
        return ConversationHandler.END

    # قراءة وتنظيف القائمة (إزالة التكرار والأسطر الفارغة)
    with open(db_file, "r") as f:
        user_ids = list(set(line.strip() for line in f if line.strip()))

    await query.edit_message_text(f"🚀 جاري الإرسال إلى {len(user_ids)} مستخدم (كل من تفاعل مع البوت)...")
    
    sent, fail = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.05) # تجنب حظر التليجرام
        except:
            fail += 1

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"✅ **اكتملت الإذاعة الشاملة**\n\n🟢 المستلمون: {sent}\n🔴 الحظر/الفشل: {fail}"
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
