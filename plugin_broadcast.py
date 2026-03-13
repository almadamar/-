import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler, 
    CallbackQueryHandler
)
from config_data import OWNER_ID

# مراحل المحادثة
AWAITING_TEXT, CONFIRM_BROADCAST = range(2)
DB_FILE = "users_data.txt"

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: 
        return ConversationHandler.END
    await update.message.reply_text("📥 **نظام الإذاعة**\n\nأرسل النص الذي تود نشره الآن:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    kb = [
        [InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_send")]
    ]
    await update.message.reply_text(
        f"📝 **معاينة الرسالة:**\n\n{update.message.text}\n\n**هل نعتمد النشر؟**", 
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم إلغاء العملية.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    
    if not os.path.exists(DB_FILE):
        await query.edit_message_text("⚠️ لا يوجد بيانات مستخدمين.")
        return ConversationHandler.END

    user_ids = []
    with open(DB_FILE, "r") as f:
        for line in f:
            if "|" in line:
                uid = line.strip().split("|")[0]
                if uid: user_ids.append(uid)
            else:
                uid = line.strip()
                if uid: user_ids.append(uid)

    await query.edit_message_text(f"🚀 جاري النشر لـ {len(user_ids)} مشترك...")
    
    sent, fail = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await context.bot.send_message(
        chat_id=OWNER_ID, 
        text=f"✅ **انتهت الإذاعة**\n🟢 نجاح: {sent}\n🔴 فشل: {fail}"
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
        per_chat=True,   # تم التغيير من per_message إلى per_chat لإصلاح التحذير
        per_user=True    # لضمان أن كل مستخدم له محادثته الخاصة
    )
    app.add_handler(conv_handler)
