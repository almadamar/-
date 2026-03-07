import os, asyncio
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# إعدادات القاعدة والمعرف الخاص بك
DB_FILE = "users.txt"
OWNER_ID = 162459553

def get_all_users():
    """قراءة المستخدمين من الملف مباشرة لضمان دقة الإحصائيات"""
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip()}

async def stats_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر عرض الإحصائيات بالعربي"""
    if update.effective_user.id != OWNER_ID: return
    
    users = get_all_users()
    await update.message.reply_text(
        f"📊 **إحصائيات البوت الحالية:**\n\n"
        f"👥 عدد المستخدمين النشطين: {len(users)}\n"
        f"📡 حالة السيرفر: متصل ✅"
    )

async def broadcast_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر الإذاعة للكل بالعربي"""
    if update.effective_user.id != OWNER_ID: return
    
    if not context.args:
        await update.message.reply_text("⚠️ **تنبيه:** يرجى كتابة نص الرسالة بعد الأمر.\nمثال: `/اذاعة نص الرسالة هنا`")
        return

    msg_to_send = " ".join(context.args)
    users = get_all_users()
    count = 0
    
    status_msg = await update.message.reply_text(f"📢 جاري بدء الإذاعة لـ {len(users)} مستخدم...")

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=msg_to_send)
            count += 1
            await asyncio.sleep(0.05) # حماية من حظر التليجرام
        except:
            continue

    await status_msg.edit_text(
        f"✅ **اكتملت عملية الإذاعة!**\n\n"
        f"📧 وصلت لـ: {count}\n"
        f"❌ فشلت لـ: {len(users) - count} (حسابات محذوفة أو محظورة)"
    )

def setup(app):
    """ربط الأوامر العربية بالبوت الأساسي"""
    app.add_handler(CommandHandler("الاحصائيات", stats_ar))
    app.add_handler(CommandHandler("اذاعة", broadcast_ar))
