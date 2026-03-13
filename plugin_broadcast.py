import asyncio
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
from bot import users_col  # استيراد المجموعة التي أعددناها بإعدادات الأمان

AWAITING_TEXT, CONFIRM_BROADCAST = range(2)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: 
        return ConversationHandler.END
    await update.message.reply_text("📥 **نظام الإذاعة السحابي**\n\nاكتب الرسالة التي تود نشرها للجميع:")
    return AWAITING_TEXT

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_msg'] = update.message.text
    kb = [
        [InlineKeyboardButton("✅ نشر للسحاب", callback_data="confirm_send")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_send")]
    ]
    await update.message.reply_text(
        f"📝 **معاينة الرسالة:**\n\n{update.message.text}\n\n**هل تود النشر الآن؟**", 
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
    
    try:
        # جلب المستخدمين مع مهلة زمنية قصيرة لتجنب التعليق
        all_users = await users_col.find().to_list(length=None)
        
        if not all_users:
            await query.edit_message_text("⚠️ لا يوجد مستخدمون مسجلون في السحاب بعد.")
            return ConversationHandler.END

        await query.edit_message_text(f"🚀 جاري النشر لـ {len(all_users)} مستخدم...")
        
        sent, fail = 0, 0
        for doc in all_users:
            try:
                await context.bot.send_message(chat_id=doc['user_id'], text=msg)
                sent += 1
                await asyncio.sleep(0.05) # حماية من حظر التليجرام
            except: 
                fail += 1

        await context.bot.send_message(
            chat_id=OWNER_ID, 
            text=f"✅ **اكتملت الإذاعة**\n🟢 نجاح: {sent}\n🔴 فشل: {fail}"
        )
    except Exception as e:
        # إذا حدث خطأ SSL هنا، سنقوم بتوضيح أن المشكلة في جلب البيانات
        await query.edit_message_text(f"❌ خطأ في قاعدة البيانات: {str(e)[:100]}...")
        
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
