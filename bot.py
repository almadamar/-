import os
import logging
import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import yt_dlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ---------------- إعدادات البوت ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553 
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

DOWNLOAD_DIR = 'downloads'
DEFAULT_POINTS = 15
REPORT_STATE, BROADCAST_STATE = range(1, 3)

user_points = {}
active_users = set()

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# ---------------- وظائف الإدارة ----------------

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(f"📊 **إحصائيات البوت:**\n\n👥 المستخدمين: {len(active_users)}\n💰 النقاط: 15 يومياً")

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text("📢 أرسل الرسالة للإذاعة:")
    return BROADCAST_STATE

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    count = 0
    for uid in active_users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=msg.chat_id, message_id=msg.message_id)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text(f"✅ تمت الإذاعة لـ {count} مستخدم.")
    return ConversationHandler.END

# ---------------- نظام النقاط ----------------
async def reset_daily_points(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_points:
        user_points[user_id] = DEFAULT_POINTS
    logging.info("♻️ تم تجديد النقاط اليومية.")

# ---------------- الأوامر ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_users.add(user_id)
    if user_id not in user_points: user_points[user_id] = DEFAULT_POINTS

    points_display = "♾ غير محدود" if user_id == OWNER_ID else f"{user_points[user_id]}"
    welcome = (f"🚀 **بوت التحميل الذكي**\n\n💰 رصيدك: {points_display} نقطة\n♻️ تجديد تلقائي كل 24 ساعة\n\n📢 القناة: {CHANNEL_LINK}")
    
    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(welcome, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        keys = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ اشترك أولاً لتفعيل البوت:", reply_markup=InlineKeyboardMarkup(keys))

# ---------------- التحميل والإبلاغ ----------------
async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 اكتب مشكلتك وسأرسلها للمطور:")
    return REPORT_STATE

async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ **بلاغ خطأ**\n👤 {user.full_name}\n🆔 `{user.id}`\n💬 {update.message.text}")
    await update.message.reply_text("✅ تم إرسال البلاغ.")
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    if not url.startswith("http") or not await is_subscribed(context.bot, user_id): return
    if user_id != OWNER_ID and user_points.get(user_id, 0) <= 0:
        await update.message.reply_text("❌ نفذت نقاطك اليومية!")
        return
    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو MP4", callback_data=f'vid|{link_id}')], [InlineKeyboardButton("🎵 صوت MP3", callback_data=f'aud|{link_id}')]]
    await update.message.reply_text(f"💰 الرصيد: {'♾' if user_id==OWNER_ID else user_points[user_id]}\nاختر النوع:", reply_markup=InlineKeyboardMarkup(keys))

async def download_logic(query, context, url, mode):
    user_id = query.from_user.id
    bot_info = await context.bot.get_me()
    msg_status = await query.edit_message_text("⏳ جاري التحميل...")
    def ytdlp_process():
        ydl_opts = {'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s', 'quiet': True}
        if mode == 'vid': ydl_opts.update({'format': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
        else: ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            final = os.path.splitext(path)[0] + ('.mp4' if mode == 'vid' else '.mp3')
            if os.path.exists(path) and path != final: os.rename(path, final)
            return final
    try:
        path = await asyncio.wait_for(asyncio.get_running_loop().run_in_executor(None, ytdlp_process), timeout=200)
        share_btn = [[InlineKeyboardButton("🚀 مشاركة الفيديو", switch_inline_query=f"@{bot_info.username}")]]
        with open(path, 'rb') as f:
            if mode == 'vid': await query.message.reply_video(video=f, caption=f"✅ @{bot_info.username}", reply_markup=InlineKeyboardMarkup(share_btn))
            else: await query.message.reply_audio(audio=f, caption=f"✅ @{bot_info.username}", reply_markup=InlineKeyboardMarkup(share_btn))
        if user_id != OWNER_ID: user_points[user_id] -= 1
        if os.path.exists(path): os.remove(path)
        await msg_status.delete()
    except:
        await msg_status.edit_text("❌ فشل التحميل.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚠️ إبلاغ عن مشكلة", callback_data="report_fail")]]))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التحقق!")
    elif "|" in query.data:
        data = query.data.split('|')
        url = context.user_data.get(data[1])
        if url: await download_logic(query, context, url, data[0])

# ---------------- نظام التشغيل المصحح لـ Render ----------------
async def main():
    app = Application.builder().token(TOKEN).build()
    
    # تشغيل المجدل داخل حلقة الأحداث (الإصلاح الجذري)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_points, 'interval', hours=24, args=[app])
    scheduler.start() #

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_report, pattern="^report_fail$"), CommandHandler('broadcast', broadcast_start)],
        states={REPORT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_text)], BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, send_broadcast)]},
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- البوت يعمل الآن بنجاح ---")
    async with app:
        await app.initialize()
        await app.start_polling()
        await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass
