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
OWNER_ID = 162459553  # معرف المطور لاستلام البلاغات
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

DOWNLOAD_DIR = 'downloads'
DEFAULT_POINTS = 15
REPORT_STATE = 1

user_points = {}
active_users = set()

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# ---------------- تجديد النقاط (كل 24 ساعة) ----------------
async def reset_daily_points(context: ContextTypes.DEFAULT_TYPE):
    for user_id in user_points: user_points[user_id] = DEFAULT_POINTS
    logging.info("♻️ تم تجديد النقاط اليومية.")

# ---------------- دوال مساعدة ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ---------------- الأوامر ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_users.add(user_id)
    bot_info = await context.bot.get_me()
    if user_id not in user_points: user_points[user_id] = DEFAULT_POINTS

    welcome = (f"🚀 **بوت التحميل الذكي**\n\n"
               f"💰 رصيدك: {user_points[user_id]} نقطة\n"
               f"♻️ تجديد تلقائي كل 24 ساعة\n\n"
               f"📢 القناة: {CHANNEL_LINK}")
    
    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(welcome, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        keys = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ اشترك أولاً لتفعيل البوت:", reply_markup=InlineKeyboardMarkup(keys))

# ---------------- نظام الإبلاغ (يظهر عند الفشل فقط) ----------------
async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 من فضلك، اكتب المشكلة التي واجهتك مع الرابط وسأرسلها للمطور:")
    return REPORT_STATE

async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    problem_text = update.message.text
    report_to_owner = (f"⚠️ **بلاغ عن فشل تحميل**\n\n"
                       f"👤 **المستخدم:** {user.full_name} (@{user.username})\n"
                       f"🆔 **ID:** `{user.id}`\n"
                       f"💬 **المشكلة:** {problem_text}")
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=report_to_owner, parse_mode='Markdown')
        await update.message.reply_text("✅ شكراً لك، تم إرسال البلاغ للمطور لتحسين الخدمة.")
    except:
        await update.message.reply_text("❌ فشل إرسال البلاغ.")
    return ConversationHandler.END

# ---------------- معالجة التحميل ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, user_id):
        await start(update, context); return

    if user_points.get(user_id, 0) <= 0:
        await update.message.reply_text("❌ نفذت نقاطك اليومية!")
        return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو MP4", callback_data=f'vid|{link_id}')],
            [InlineKeyboardButton("🎵 صوت MP3", callback_data=f'aud|{link_id}')]]
    await update.message.reply_text(f"💰 الرصيد: {user_points[user_id]}\nاختر النوع:", reply_markup=InlineKeyboardMarkup(keys))

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
        caption = f"✅ تم التحميل بنجاح!\n\n🤖 @{bot_info.username}\n📢 القناة الرسمية"
        share_btn = [[InlineKeyboardButton("🚀 مشاركة الفيديو", switch_inline_query=f"@{bot_info.username}")]]
        
        with open(path, 'rb') as f:
            if mode == 'vid': await query.message.reply_video(video=f, caption=caption, reply_markup=InlineKeyboardMarkup(share_btn))
            else: await query.message.reply_audio(audio=f, caption=caption, reply_markup=InlineKeyboardMarkup(share_btn))
        
        user_points[user_id] -= 1
        if os.path.exists(path): os.remove(path)
        await msg_status.delete()
    except Exception:
        # هنا تظهر رسالة الفشل مع زر التبليغ
        fail_keys = [[InlineKeyboardButton("⚠️ إبلاغ عن مشكلة", callback_data="report_fail")]]
        await msg_status.edit_text("❌ عذراً، فشل التحميل. قد يكون الرابط غير مدعوم أو خاص.", reply_markup=InlineKeyboardMarkup(fail_keys))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التحقق!")
        else: await query.answer("⚠️ اشترك أولاً!", show_alert=True)
    elif "|" in query.data:
        data = query.data.split('|')
        url = context.user_data.get(data[1])
        if url: await download_logic(query, context, url, data[0])

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    # معالج الإبلاغ يعمل فقط عند الضغط على زر التبليغ
    report_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_report, pattern="^report_fail$")],
        states={REPORT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_text)]},
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_points, 'interval', hours=24, args=[app])
    scheduler.start()

    app.add_handler(report_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    app.run_polling()
