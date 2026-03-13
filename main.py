import logging
import music_archiver  # استيراد ملف الأغاني المطور
from telegram.ext import Application, CallbackQueryHandler

# --- إعدادات التسجيل لمراقبة أداء البوت في Render ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- بيانات البوت الجديدة ---
TOKEN = "8539861357:AAG-GMmy5AGYpZAQ14ZeNymnAYlTjeZnKUM"

async def post_init(application: Application):
    """ تنظيف الـ Webhook القديم لضمان استجابة البوت فور تشغيله """
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("✅ تم تنظيف الجلسة بنجاح.. البوت مستعد الآن.")

def main():
    """ المحرك الرئيسي للبوت """
    print("🚀 جاري تشغيل النظام المتكامل (التحميل + الأرشفة + الخدمات)...")

    # إنشاء التطبيق وربطه ببياناتك
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # --- 1. ربط موديول الموسيقى والخدمات ---
    # هذا السطر يربط (استلام الروابط + الأزرار + الاشتراك الإجباري)
    try:
        music_archiver.setup_music_module(application)
        print("🎵 نظام الأرشفة والخدمات: متصل.")
    except Exception as e:
        print(f"❌ خطأ في ربط موديول الموسيقى: {e}")

    # --- 2. ربط الإضافات القديمة (Plugins) ---
    # إذا كان لديك ملفات قديمة تريد تشغيلها في نفس الوقت (مثل البث):
    # try:
    #     import plugin_broadcast
    #     plugin_broadcast.setup(application)
    # except: pass

    # --- 3. تشغيل البوت بنظام Polling ---
    # نظام drop_pending_updates يضمن أن البوت لن ينفذ أوامر قديمة أُرسلت أثناء توقفه
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
