# المشروع الثاني - ملف الميزات الإضافية المطور
# اسم الملف: plugin_extras.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# إعدادات المطور للمشروع الثاني
OWNER_ID = 162459553 
BROADCAST_STATE = 1

# --- [1] ميزة الإذاعة (Broadcast) للمطور فقط ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return # تجاهل إذا لم يكن المطور
    
    await update.message.reply_text("📢 **أهلاً مطورنا عادل..**\nأرسل الآن الرسالة التي تريد إذاعتها (نص، صورة، فيديو، ملف):")
    return BROADCAST_STATE

async def execute_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ملاحظة: الكود الأساسي يجب أن يجمع اليوزرات في active_users
    # هنا سنفترض الوصول للمستخدمين النشطين (يمكن تطوير نظام تخزين مشترك مستقبلاً)
    from bot import active_users # استيراد قائمة المستخدمين من المحرك الأساسي
    
    msg = update.message
    success = 0
    fail = 0
    
    status_msg = await msg.reply_text("⏳ جاري الإذاعة لجميع المستخدمين...")
    
    for user_id in active_users:
        try:
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            success += 1
            await asyncio.sleep(0.05) # حماية من الحظر
        except:
            fail += 1
            continue
            
    await status_msg.edit_text(f"✅ **اكتملت الإذاعة:**\n\n👤 نجاح: {success}\n❌ فشل: {fail}")
    return ConversationHandler.END

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 تم إلغاء العملية.")
    return ConversationHandler.END

# --- [2] ميزة الإحصائيات (معدلة) ---
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot import active_users
    if update.effective_user.id != OWNER_ID: return
    
    stats_text = (
        f"📊 **إحصائيات البوت الشاملة:**\n\n"
        f"👥 المستخدمين النشطين: {len(active_users)}\n"
        f"🔌 نظام المشاريع: متصل وجاهز\n"
        f"🛠 المشروع الحالي: `plugin_extras.py`"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# --- [3] ميزة مساعدة الميزات ---
async def help_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_owner = update.effective_user.id == OWNER_ID
    text = "🛠 **قائمة الميزات الإضافية:**\n\n"
    if is_owner:
        text += "📢 /broadcast - إذاعة رسالة للكل\n"
        text += "📊 /stats - إحصائيات المطور\n\n"
    
    text += "💡 أرسل أي رابط لتحميله مباشرة (720p)."
    await update.message.reply_text(text, parse_mode='Markdown')

# --- [4] دالة التسجيل التلقائي ---
def setup(app):
    # إعداد المحادثة للإذاعة
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, execute_broadcast)]
        },
        fallbacks=[CommandHandler("cancel", cancel_action)]
    )
    
    app.add_handler(broadcast_handler)
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_features))
    
    print("📢 تم دمج ميزة الإذاعة والإحصائيات بنجاح!")
