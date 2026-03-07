import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler

OWNER_ID = 162459553
DB_FILE = "users.txt"

def get_users_list():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return f.read().splitlines()

async def kmr_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المطور kmr"""
    if update.effective_user.id != OWNER_ID: return
    
    count = len(get_users_list())
    keyboard = [
        [InlineKeyboardButton("📊 تحديث الأرقام", callback_data="adm_refresh")],
        [InlineKeyboardButton("📂 تحميل النسخة الاحتياطية", callback_data="adm_backup")],
        [InlineKeyboardButton("📢 إرسال إذاعة", callback_data="adm_bc")]
    ]
    
    await update.message.reply_text(
        f"🛠 **لوحة تحكم KMR**\n\n👥 عدد المشتركين المسجلين: `{count}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار الإدارة مع حماية من تداخل التحميل"""
    query = update.callback_query
    if query.from_user.id != OWNER_ID or "|" in query.data: return
    
    await query.answer()
    
    if query.data == "adm_refresh":
        count = len(get_users_list())
        await query.edit_message_text(f"✅ تم التحديث!\n👥 المشتركين: `{count}`", 
                                      reply_markup=query.message.reply_markup)
    
    elif query.data == "adm_backup":
        if os.path.exists(DB_FILE):
            await query.message.reply_document(document=open(DB_FILE, 'rb'), 
                                               caption="💾 نسخة مستخدمي البوت الحالية.")
        else:
            await query.message.reply_text("❌ الملف غير موجود بعد.")

    elif query.data == "adm_bc":
        await query.message.reply_text("💡 أرسل الرسالة بالشكل التالي:\n`/اذاعة نص رسالتك هنا`")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الإذاعة المعرب"""
    if update.effective_user.id != OWNER_ID or not context.args: return
    
    msg = " ".join(context.args)
    users = get_users_list()
    count = 0
    status = await update.message.reply_text(f"⏳ جاري الإذاعة لـ {len(users)}...")
    
    for u_id in users:
        try:
            await context.bot.send_message(int(u_id), msg)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await status.edit_text(f"✅ اكتملت الإذاعة! وصل لـ {count} مستخدم.")

def setup(app):
    # تفعيل الاستجابة لـ kmr وخدماتي
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'(?i)^kmr$|^خدماتي$'), kmr_panel))
    app.add_handler(CommandHandler("اذاعة", broadcast_command))
    app.add_handler(CallbackQueryHandler(admin_actions))
