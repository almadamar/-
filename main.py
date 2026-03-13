import logging
import music_archiver
from telegram.ext import Application

# إعداد السجلات لمراقبة البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- بيانات البوت الجديد ---
TOKEN = "8044419232:AAHCxEyw-mHBz-Vu9pTrihA8PfjcVODPU5E"

async def post_init(application: Application):
    """ تنظيف الجلسات القديمة عند التشغيل """
    await application.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Auto Music Hub جاهز للعمل الآن!")

def main():
    # بناء التطبيق
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # ربط موديول الأرشفة والخدمات
    try:
        music_archiver.setup_music_module(application)
        print("🎵 تم تفعيل نظام الأرشفة بنجاح.")
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")

    # بدء التشغيل
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
