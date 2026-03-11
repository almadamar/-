from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import OWNER_ID

async def monitor_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد من وجود رسالة نصية
    if not update.message or not update.message.text:
        return

    text = update.message.text
    # نراقب فقط الروابط
    if not text.startswith("http"):
        return

    user = update.effective_user
    username = f"@{user.username}" if user.username else "لا يوجد"
    
    # صياغة الرسالة كنص عادي (بدون Markdown لتجنب أخطاء الرموز)
    report = (
        "🕵️‍♂️ كشف تحرك جديد:\n\n"
        f"👤 الاسم: {user.first_name}\n"
        f"🏷 اليوزر: {username}\n"
        f"🆔 الآيدي: {user.id}\n"
        f"🔗 الرابط:\n{text}"
    )

    try:
        # إرسال الرسالة بدون parse_mode لتجنب خطأ الـ entities
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=report,
            disable_web_page_preview=True
        )
        print(f"✅ Monitor: Report sent successfully to {OWNER_ID}")
    except Exception as e:
        print(f"❌ Monitor Error: {e}")

def setup(app):
    # استخدام group=-3 لضمان الأولوية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_activity), group=-3)
