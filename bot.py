import os
import logging
import datetime
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, ConversationHandler
import yt_dlp
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ---------------- [1] الإعدادات ----------------
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

# ---------------- [2] وظائف التحقق والإدارة ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def reset_daily_points():
    for user_id in user_points:
        user_points[user_id] = DEFAULT_POINTS
    logging.info("♻️ تم تجديد النقاط اليومية.")

# ---------------- [3] الأوامر الرئيسية ----------------
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

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(f"📊 **إحصائيات البوت:**\n\n👥 المستخدمين: {len(active_users)}\n💰 النقاط: 15 يومياً")

# ---------------- [4] معالجة الرسائل والتحميل ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, user_id): return
    
    if user_id != OWNER_ID and user_points.get(user_id, 0) <= 0:
        return await update.message.reply_text("❌ نفذت نقاطك اليومية!")

    link_id = str(random.randint(1000, 9999))
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو MP4", callback_data=f'vid|{link_id}'),
             InlineKeyboardButton("🎵 صوت MP3", callback_data=f'aud|{link_id}')]]
    await update.message.reply_text(f"💰 الرصيد: {user_points.get(user_id, DEFAULT_POINTS)}\nاختر النوع:", reply_markup=InlineKeyboardMarkup(keys))

async def download_logic(query, context, url, mode):
    user_id = query.from_user.id
    msg_status = await query.edit_message_text("⏳ جاري التحميل...")
    
    def ytdlp_process():
        ydl_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'],
            'quiet': True
        }
        if mode == 'aud':
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    try:
        path = await asyncio.get_running_loop().run_in_executor(None, ytdlp_process)
        # تصحيح الامتداد للملف النهائي
        final_path = path if mode == 'vid' else os.path.splitext(path)[0] + '.mp3'
        
        with open(final_path, 'rb') as f:
            if mode == 'vid': await query.message.reply_video(video=f, caption="✅ تم التحميل")
            else: await query.message.reply_audio(audio=f, caption="✅ تم التحميل")
            
        if user_id != OWNER_ID: user_points[user_id] -= 1
        if os.path.exists(final_path): os.remove(final_path)
        await msg_status.delete()
    except:
        await msg_status.edit_text("❌ فشل التحميل.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.edit_message_text("✅ تم التحقق! أرسل الرابط الآن.")
    elif "|" in query.data:
        mode, link_id = query.data.split('|')
        url = context.user_data.get(link_id)
        if url: await download_logic(query, context, url, mode)

# ---------------- [5] تشغيل التطبيق ----------------
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    
    # إعداد المجدل لتصفير النقاط
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_points, 'interval', hours=24)
    scheduler.start()

    # الروابط والأوامر
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- البوت يعمل الآن بنجاح وبشكل كامل ---")
    app.run_polling(drop_pending_updates=True)
