import os
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import OWNER_ID

async def monitor_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد أن الرسالة تحتوي على نص ورابط
    text = update.message.text
    if not text or not text.startswith("http"):
        return

    # استخراج معلومات المستخدم
    user = update.effective_user
    username = f"@{user.username}" if user.username else "بدون يوزر"
    
    # صياغة التقرير الاحترافي
    report = (
        f"🕵️‍♂️ **تقرير نشاط جديد:**\n\n"
        f"👤 **الاسم:** {user.first_name}\n"
        f"🏷 **اليوزر:** {username}\n"
        f"🆔 **الآيدي:** `{user.id}`\n"
        f"🔗 **الرابط المرسل:**\n{text}\n\n"
        f"⏳ _جاري معالجته بواسطة الملحقات الأخرى..._"
    )

    # إرسال التقرير إليك فقط في محادثة البوت الخاصة
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=report,
            parse_mode='Markdown',
            disable_web_page_preview=True # لكي لا تظهر معاينة الرابط وتزحم المحادثة
        )
    except Exception as e:
        print(f"Monitor Error: {e}")

def setup(app):
    # نستخدم Group=-2 لضمان أن هذا الملحق يلقط الرابط قبل أي ملحق آخر
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_activity), group=-2)
