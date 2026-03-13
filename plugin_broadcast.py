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
DB_FILE = "users_data.txt" # الملف الجديد الذي يحتوي على التاريخ

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: 
        return ConversationHandler.END
    await update.message.reply_text("📥 **نظام الإذاعة المطور**\n\nاكتب رسالتك الآن:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    kb = [
        [InlineKeyboardButton("✅ تأكيد الإرسال للكل", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_send")]
    ]
    await update.message.reply_text(
        f"📝 **معاينة الرسالة:**\n\n{update.message.text}\n\n**هل أنت متأكد من النشر؟**", 
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CONFIRM_BROADCAST

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_send":
        await query.edit_message_text("❌ تم إلغاء الإذاعة.")
        return ConversationHandler.END

    msg = context.user_data.get('broadcast_msg')
    
    if not os.path.exists(DB_FILE):
        await query.edit_message_text("⚠️ لا يوجد مشتركين في قاعدة البيانات حتى الآن.")
        return ConversationHandler.END

    # قراءة الملف واستخراج الآيديات فقط
    user_ids = []
    with open(DB_FILE, "r") as f:
        for line in f:
            if "|" in line:
                # نأخذ الجزء قبل العلامة | وهو الآيدي
                uid = line.strip().split("|")[0]
                if uid: user_ids.append(uid)
            else:
                # إذا كان السطر آيدي فقط بدون تاريخ (لضمان التوافق)
                uid = line.strip()
                if uid: user_ids.append(uid)

    if not user_ids:
        await query.edit_message_text("⚠️ قاعدة البيانات فارغة.")
        return ConversationHandler.END

    await query.edit_message_text(f"🚀 جاري الإرسال إلى {len(user_ids)} مشترك...")
    
    sent, fail = 0, 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            sent += 1
            await asyncio.sleep(0.05) # تأخير لتجنب حظر التليجرام
        except Exception:
            fail += 1

    await context.bot.send_message(
        chat_id=OWNER_ID, 
        text=f"✅ **اكتملت الإذاعة بنجاح**\n🟢 نجاح: {sent}\n🔴 فشل: {fail}"
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
        per_message=True
    )
    app.add_handler(conv_handler)
