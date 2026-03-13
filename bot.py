import os, importlib, asyncio, datetime, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    ApplicationHandlerStop 
)
# تأكد من وجود SECOND_TOKEN و REQUIRED_CHANNEL_ID في config_data
from config_data import TOKEN, SECOND_TOKEN, REQUIRED_CHANNEL_ID, CHANNEL_LINK, OWNER_ID, DOWNLOAD_DIR

# --- 1. إعداد نظام المراقبة والتعقب (Logging) ---
logging.basicConfig(
    format='%(asctime)s - 🛠️ [%(levelname)s]: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)

DB_FILE = "users_data.txt"

# --- 2. صائد الأخطاء الشامل ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="❌ حدث خطأ فني أثناء المعالجة:", exc_info=context.error)

# --- 3. نظام الاشتراك الإجباري الموحد ---
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return True
    user_id = update.effective_user.id
    if user_id == OWNER_ID: return True

    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except: pass

    kb = [[InlineKeyboardButton("📢 اشترك في القناة الرسمية", url=CHANNEL_LINK)]]
    await update.message.reply_text(
        "⚠️ **عذراً عزيزي، يجب عليك الاشتراك في قناة المنظومة الرسمية أولاً لتتمكن من استخدام البوتات.**",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )
    return False

# --- 4. دالة التوجيه الذكي (لمنع تداخل البوت الأساسي) ---
async def redirect_to_archiver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    url = update.message.text.lower()
    # كافة المنصات التي طلبت توجيهها للبوت الثاني
    target_sites = [
        "soundcloud.com", "pinterest.com", "pin.it", "snapchat.com", ".mp3", 
        "v.snapchat.com", "spotify.com", "apple.com", "deezer.com", 
        "audiomack.com", "anghami.com", "qobuz.com", "music.youtube"
    ]
    
    if any(site in url for site in target_sites):
        if update.effective_chat.type in ['group', 'supergroup']:
            user_name = update.effective_user.first_name if update.effective_user else "عزيزي"
            text = (
                f"👋 أهلاً {user_name}!\n\n"
                f"هذه الروابط (صوتيات/أرشفة) يتم معالجتها حصراً عبر بوت الأرشفة الخاص بنا 📥✨"
            )
            keyboard = [[InlineKeyboardButton("🚀 اذهب إلى بوت الأرشفة", url="https://t.me/AutoMusicHubBot")]]
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            raise ApplicationHandlerStop 

# --- 5. نظام التذكير وتسجيل النشاط (ميزتك السابقة) ---
async def global_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else (update.callback_query.from_user.id if update.callback_query else None)
    if user_id:
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        data = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                for l in f:
                    if "|" in l: uid, d = l.strip().split("|"); data[uid] = d
        data[str(user_id)] = now
        with open(DB_FILE, "w") as f:
            for uid, d in data.items(): f.write(f"{uid}|{d}\n")

async def reminder_task(context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(DB_FILE): return
    now = datetime.datetime.now()
    with open(DB_FILE, "r") as f: lines = f.readlines()
    for line in lines:
        try:
            uid, last_date_str = line.strip().split("|")
            if (now - datetime.datetime.strptime(last_date_str, "%Y-%m-%d")).days == 5:
                try: await context.bot.send_message(chat_id=int(uid), text="مرحباً! ماذا تفكر اليوم بالتحميل؟ 📥✨")
                except: pass
        except: continue

# --- 6. دمج الملحقات والمحركات ---
async def post_init_bot1(application):
    application.job_queue.run_repeating(reminder_task, interval=86400, first=10)
    # إضافة فحص الاشتراك للبوت الأول
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_subscription), group=-3)
    
    plugins = ['plugin_monitor', 'plugin_broadcast', 'plugin_search', 'plugin_pro', 'plugin_youtube', 'plugin_extras']
    for p in plugins:
        try:
            module = importlib.import_module(p)
            module.setup(application)
            logger.info(f"✅ تم تفعيل الملحق: {p}")
        except Exception as e: logger.error(f"❌ خطأ {p}: {e}")

async def post_init_bot2(application):
    # إضافة فحص الاشتراك للبوت الثاني
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_subscription), group=-3)
    try:
        import music_archiver
        music_archiver.setup_music_module(application)
        logger.info("🚀 نظام الأرشفة جاهز.")
    except Exception as e: logger.error(f"❌ خطأ موديول الموسيقى: {e}")

# --- 7. تشغيل المنظومة المزدوجة ---
async def main():
    bot1_app = ApplicationBuilder().token(TOKEN).post_init(post_init_bot1).build()
    bot2_app = ApplicationBuilder().token(SECOND_TOKEN).post_init(post_init_bot2).build()

    await bot1_app.initialize()
    await bot1_app.start()
    await bot1_app.updater.start_polling(drop_pending_updates=True)

    await bot2_app.initialize()
    await bot2_app.start()
    await bot2_app.updater.start_polling(drop_pending_updates=True)

    # إضافة المعالجات العامة للبوت الأساسي كما في كودك السابق
    bot1_app.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), redirect_to_archiver), group=0)
    bot1_app.add_handler(MessageHandler(filters.ALL, global_tracker), group=-1)
    bot1_app.add_handler(CallbackQueryHandler(global_tracker), group=-1)

    logger.info("⚡ المنظومة الموحدة تعمل الآن بكامل طاقتها.")
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
