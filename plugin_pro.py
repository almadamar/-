import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

DB_FILE = "users.txt"
OWNER_ID = 162459553

def get_all_users():
    """قراءة عدد المستخدمين بدقة"""
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip()}

async def admin_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الخدمات الإدارية للمطور فقط"""
    if update.effective_user.id != OWNER_ID: return
    
    users_count = len(get_all_users())
    
    keyboard = [
        [InlineKeyboardButton("📊 تحديث الإحصائيات", callback_data="refresh_stats")],
        [InlineKeyboardButton("📢 إرسال إذاعة (BC)", callback_data="start_bc")],
        [InlineKeyboardButton("⚙️ إعدادات السيرفر", callback_data="server_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🛠 **قائمة خدمات المطور:**\n\n"
        f"👥 عدد المستخدمين الحالي: `{users_count}`\n"
        "━━━━━━━━━━━━━━\n"
        "اختر من الأزرار أدناه للتحكم في البوت:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات أزرار قائمة الخدمات"""
    query = update.callback_query
    if update.effective_user.id != OWNER_ID: return
    
    await query.answer()
    
    if query.data == "refresh_stats":
        users_count = len(get_all_users())
        await query.edit_message_text(
            f"✅ تم التحديث!\n👥 عدد المستخدمين الآن: `{users_count}`",
            reply_markup=query.message.reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "start_bc":
        await query.message.reply_text("💡 لإرسال إذاعة، استخدم الأمر:\n`/اذاعة` متبوعاً برسالتك.")

    elif query.data == "server_info":
        await query.message.reply_text("🖥 **معلومات السيرفر:**\nالمنطقة: Frankfurt (Render Free)\nالحالة: يعمل ✅")

def setup(app):
    """تسجيل الأوامر العربية الجديدة"""
    app.add_handler(CommandHandler("خدماتي", admin_services))
    app.add_handler(CommandHandler("الاحصائيات", admin_services)) # اختصار إضافي
    app.add_handler(CommandHandler("اذاعة", broadcast_ar)) # دالة الإذاعة السابقة
    app.add_handler(CallbackQueryHandler(handle_admin_buttons))
