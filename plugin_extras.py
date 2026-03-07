from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب عند تشغيل البوت"""
    user_name = update.effective_user.first_name
    text = (
        f"اهلا بك يا {user_name} في بوت التحميل الذكي 🤖\n\n"
        "✨ **ماذا يمكنني أن أفعل؟**\n"
        "يمكنك إرسال روابط من المنصات التالية للتحميل:\n"
        "🔹 تيك توك (بدون حقوق)\n"
        "🔹 إنستغرام (ريلز وفيديو)\n"
        "🔹 فيسبوك\n\n"
        "📥 **كيفية الاستخدام:**\n"
        "فقط أرسل الرابط وسأقوم بعرض خيارات التحميل لك."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def help_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة بالعربي"""
    text = (
        "📖 **قائمة المساعدة:**\n\n"
        "📍 /start - لتشغيل البوت والترحيب\n"
        "📍 /مساعدة - لعرض هذه القائمة\n\n"
        "⚠️ **ملاحظة:** إذا واجهت مشكلة في التحميل، تأكد أن الحساب صاحب الفيديو ليس 'خاصاً' (Private)."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

def setup(app):
    """تسجيل الأوامر العربية في النظام الأساسي"""
    app.add_handler(CommandHandler("start", start_ar))
    app.add_handler(CommandHandler("مساعدة", help_ar))
