import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from config_data import OWNER_ID

AWAITING_TEXT, CONFIRM_BROADCAST = range(2)
USERS_FILE = "users.txt"

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return ConversationHandler.END
    await update.message.reply_text("📥 **الإذاعة المحلية**\n\nاكتب رسالتك:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    kb = [[InlineKeyboardButton("✅ إرسال للجميع", callback_data="confirm_send")], [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_send")]]
    await update.message.reply_text(f"📝 معاينة:\n\n{update.message.text}", reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    
    if not os.path.exists(USERS_FILE):
        await query.edit_message_text("⚠️ لا يوجد مشتركين بعد.")
        return ConversationHandler.END

    with open(USERS_FILE, "r") as f:
        all_users = f.read().splitlines()

    await query.edit_message_text(f"🚀 جاري الإرسال لـ {len(all_users)} مشترك...")
    
    sent, fail = 0, 0
    for user_id in all_users:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=msg)
            sent += 1
            await asyncio.sleep(0.05)
        except: fail += 1

    await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ اكتملت الإذاعة\n🟢 نجاح: {sent}\n🔴 فشل: {fail}")
    return ConversationHandler.END

def setup(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            AWAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            CONFIRM_BROADCAST: [CallbackQueryHandler(execute_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_message=True
    )
    app.add_handler(conv_handler)
