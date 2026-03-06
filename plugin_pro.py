# ==========================================
# المشروع الثالث: استعلام الخدمات والميزات الاحترافية
# المطور: أنمار (Anmar)
# الملف: plugin_pro.py
# ==========================================

import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes

# معرف المطور (أنمار) للتحكم الخاص
OWNER_ID = 162459553 

# --- [1] قائمة الخدمات الشاملة (للمستخدمين) ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض كافة الخدمات المتاحة في البوت"""
    help_text = (
        "🚀 **مرحباً بك في بوت أنمار للتحميل الشامل!**\n\n"
        "إليك قائمة بالخدمات التي أقدمها لك بجودة **720p**:\n\n"
        "🎬 **تيك توك (TikTok):**\n"
        "• تحميل تلقائي بدون علامة مائية (Watermark).\n\n"
        "📸 **إنستغرام (Instagram):**\n"
        "• تحميل الريلز، القصص، والمنشورات بصيغة MP4.\n\n"
        "📺 **يوتيوب (YouTube):**\n"
        "• تحميل الفيديوهات بدقة 720p.\n"
        "• خيار استخراج الصوت MP3 بجودة عالية.\n\n"
        "🐦 **تويتر / إكس (X):**\n"
        "• تحميل المقاطع بضغطة واحدة.\n\n"
        "💡 **طريقة الاستخدام:** فقط أرسل الرابط، وسيتكفل بوت أنمار بالباقي!"
    )
    
    # أزرار تفاعلية تحت قائمة الخدمات
    keyboard = [
        [InlineKeyboardButton("🔗 مشاركة البوت", url="https://t.me/share/url?url=https://t.me/Down2024_bot")],
        [InlineKeyboardButton("👨‍💻 المطور", url="https://t.me/AN_AZ22")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

# --- [2] ميزة الاستعلام والتعرف التلقائي ---
async def auto_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إشعار المستخدم بنوع الرابط قبل التحميل"""
    text = update.message.text
    if not text or not text.startswith("http"):
        return

    if "tiktok.com" in text:
        await update.message.reply_text("✅ **أنمار يحللها:** رابط تيك توك.. جاري سحبه بدون علامة مائية.")
    elif "instagram.com" in text:
        await update.message.reply_text("✅ **أنمار يحللها:** رابط إنستغرام.. جاري معالجة الفيديو بجودة 720p.")
    elif "youtube.com" in text or "youtu.be" in text:
        await update.message.reply_text("✅ **أنمار يحللها:** رابط يوتيوب.. جاري التحضير بصيغة MP4.")

# --- [3] دالة الربط التلقائي (Setup) ---
def setup(app):
    """ربط المشروع الثالث بالمحرك الأساسي"""
    
    # أمر المساعدة العام للاستعلام عن الخدمات
    app.add_handler(CommandHandler("help", help_command))
    
    # معالج الاستعلام التلقائي للروابط
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(re.compile(r'tiktok|instagram|youtube|youtu\.be|x\.com|twitter', re.IGNORECASE)),
        auto_info_handler
    ), group=-1)

    print("🚀 [المشروع الثالث] تم تفعيل خدمات أنمار بنجاح!")
