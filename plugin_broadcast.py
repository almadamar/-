import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from config_data import OWNER_ID
from bot import users_col 

AWAITING_TEXT, CONFIRM_BROADCAST = range(2)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return ConversationHandler.END
    await update.message.reply_text("📥 **نظام الإذاعة السحابي**\n\nاكتب الرسالة المراد نشرها:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    kb = [[InlineKeyboardButton("✅ نشر للسحاب", callback_data="confirm_send")], [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_send")]]
    await update.message.reply_text(f"📝 **المعاينة:**\n\n{update.message.text}\n\n**تأكيد النشر؟**", reply_markup=InlineKeyboardMarkup(kb))
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    try:
        # جلب القائمة من السحاب
        all_users = await users_col.find().to_list(length=None)
        await query.edit_message_text(f"🚀 جاري النشر لـ {len(all_users)} مستخدم...")
        
        sent, fail = 0, 0
        for doc in all_users:
            try:
                await context.bot.send_message(chat_id=doc['user_id'], text=msg)
                sent += 1
                await asyncio.sleep(0.05)
            except: fail += 1
        await context.bot.send_message(chat_id=OWNER_ID, text=f"✅ اكتمل النشر\n🟢 نجاح: {sent}\n🔴 فشل: {fail}")
    except Exception as e:
        await query.edit_message_text(f"❌ فشل الاتصال بالسحاب: {e}")
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
