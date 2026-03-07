import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler

# إعدادات المطور وقاعدة البيانات
DB_FILE = "users.txt"
OWNER_ID = 162459553

def get_all_users():
    """قراءة المستخدمين من الملف"""
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip()}

async def kmr_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تفعيل لوحة التحكم عند كتابة كلمة kmr"""
    # التحقق من هوية المطور والكلمة السرية
    if update.effective_user.id != OWNER_ID: return
    
    text = ""
    if update.message and update.message.text:
        text = update.message.text.lower()
    
    # الاستجابة لـ kmr أو /kmr أو /خدماتي
    if 'kmr' in text or 'خدماتي' in text:
        users_count = len(get_all_users())
        
        keyboard = [
            [InlineKeyboardButton("📊 تحديث الإحصائيات", callback_data="refresh_stats")],
            [InlineKeyboardButton("📢 إرسال إذاعة (BC)", callback_data="start_bc")],
            [InlineKeyboardButton("🌐 حالة السيرفر", callback_data="server_status")]
        ]
        
        reply_text = (
            "🛠 **لوحة تحكم KMR الذكية**\n"
            "━━━━━━━━━━━━━━\n"
            f"👤 المطور: أنمار\n"
            f"👥 المشتركون: `{users_count}`\n"
            f"📡 المنطقة: Frankfurt (Render)\n"
            "━━━━━━━━━━━━━━\n"
            "اختر من الأزرار للتحكم:"
        )
        
        await update.message.reply_text(
            reply_text, 
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار لوحة التحكم"""
    query = update.callback_query
    if query.from_user.id != OWNER_ID: return
    
    await query.answer()
    
    if query.data == "refresh_stats":
        users_count = len(get_all_users())
        await query.edit_message_text(
            f"✅ تم التحديث!\n👥 عدد المستخدمين الآن: `{users_count}`",
            reply_markup=query.message.reply_markup,
            parse_mode='Markdown'
        )
    
    elif query.data == "start_bc":
        await query.message.reply_text("💡 لإرسال إذاعة، اكتب الأمر كالتالي:\n`/اذاعة` متبوعاً بنص رسالتك.")

    elif query.data == "server_status":
        await query.message.reply_text("🖥 **حالة السيرفر:**\nالحالة: يعمل ✅\nالخطة: المجانية (Render Free)")

async def broadcast_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة الإذاعة العربية"""
    if update.effective_user.id != OWNER_ID: return
    
    if not context.args:
        await update.message.reply_text("⚠️ اكتب الرسالة بعد الأمر: `/اذاعة السلام عليكم`")
        return
    
    users = get_all_users()
    msg_text = " ".join(context.args)
    count = 0
    status = await update.message.reply_text(f"⏳ جاري بدء الإذاعة لـ {len(users)}...")
    
    for u_id in users:
        try:
            await context.bot.send_message(u_id, msg_text)
            count += 1
            await asyncio.sleep(0.05) # حماية من الحظر
        except: continue
        
    await status.edit_text(f"✅ اكتملت الإذاعة!\n📧 استلمها بنجاح: {count}")

def setup(app):
    """ربط الملحق بالبوت الأساسي"""
    # الاستماع لكلمة kmr كـ رسالة عادية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, kmr_panel))
    # الاستماع لـ /kmr و /خدماتي و /الاحصائيات كـ أوامر
    app.add_handler(CommandHandler("kmr", kmr_panel))
    app.add_handler(CommandHandler("خدماتي", kmr_panel))
    app.add_handler(CommandHandler("الاحصائيات", kmr_panel))
    # أمر الإذاعة
    app.add_handler(CommandHandler("اذاعة", broadcast_ar))
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(handle_admin_callbacks))
