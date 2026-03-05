import os
import logging
import datetime
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- إعدادات البوت ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
DEV_USERNAME = "@AN_AZ22"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 52428800  # 50 MB
COOLDOWN_SECONDS = 5

# تخزين البيانات في الذاكرة
active_users = set()
download_history = {} # سجل المستخدمين {user_id: [links]}
total_downloads_count = 0 # إحصائية للمطور

logging.basicConfig(level=logging.INFO)

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

user_cooldown = {}

# ---------------- دوال مساعدة ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def check_cooldown(user_id):
    now = datetime.datetime.now()
    if user_id in user_cooldown:
        diff = (now - user_cooldown[user_id]).total_seconds()
        if diff < COOLDOWN_SECONDS:
            return False, int(COOLDOWN_SECONDS - diff)
    user_cooldown[user_id] = now
    return True, 0

# ---------------- الأوامر ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_users.add(user_id)
    
    welcome_msg = (
        "🚀 **أهلاً بك في بوت التحميل المطور!**\n\n"
        "✅ البوت يعمل الآن مع ميزة السجل الشخصي.\n"
        "📜 عرض سجلك: /history\n"
        "🚀 أرسل رابط الفيديو للتحميل مباشرة."
    )

    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    else:
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ تم الاشتراك، ابدأ الآن", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ يجب الاشتراك أولاً تفعيل البوت:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- عرض سجل التحميل للمستخدم ---
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = download_history.get(user_id, [])
    
    if not history:
        await update.message.reply_text("📭 سجلك فارغ حالياً. ابدأ بالتحميل أولاً!")
        return
    
    msg = "📜 **آخر 5 تحميلات قمت بها:**\n\n"
    for i, link in enumerate(history[-5:], 1):
        msg += f"{i}- {link}\n"
    await update.message.reply_text(msg, disable_web_page_preview=True, parse_mode='Markdown')

# --- إحصائيات للمطور فقط ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(
        f"📊 **إحصائيات البوت:**\n\n"
        f"👥 المستخدمين النشطين: {len(active_users)}\n"
        f"📥 إجمالي التحميلات: {total_downloads_count}",
        parse_mode='Markdown'
    )

# --- إذاعة للمطور ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = "📢 **إشعار من الإدارة:** تم تحديث البوت وإضافة ميزة السجل `/history`!"
    for user_id in active_users:
        try: await context.bot.send_message(chat_id=user_id, text=msg)
        except: continue
    await update.message.reply_text("✅ تم الإرسال للجميع.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_users.add(user_id)
    url = update.message.text
    if not url.startswith("http"): return

    if not await is_subscribed(context.bot, user_id):
        await start(update, context)
        return

    allowed, wait_time = check_cooldown(user_id)
    if not allowed:
        await update.message.reply_text(f"⏳ انتظر {wait_time} ثواني.")
        return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو MP4", callback_data=f'vid|{link_id}')],
            [InlineKeyboardButton("🎵 صوت MP3", callback_data=f'aud|{link_id}')]]
    await update.message.reply_text("📥 اختر النوع:", reply_markup=InlineKeyboardMarkup(keys))

# ---------------- منطق التحميل ----------------
async def download_logic(query, context, url, mode):
    global total_downloads_count
    user_id = query.from_user.id
    await query.edit_message_text("⏳ جاري التحميل...")

    def ytdlp_download():
        ydl_opts = {'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', 'quiet': True}
        if mode.startswith('vid'):
            ydl_opts.update({'format': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'merge_output_format': 'mp4'})
        else:
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode.startswith('vid'):
                final = os.path.splitext(filename)[0] + '.mp4'
                if os.path.exists(filename) and filename != final: os.rename(filename, final)
                return final
            return os.path.splitext(filename)[0] + '.mp3'

    try:
        file_path = await asyncio.get_running_loop().run_in_executor(None, ytdlp_download)
        with open(file_path, 'rb') as f:
            if mode.startswith('vid'): await query.message.reply_video(video=f, caption=f"✅ تم التحميل\n👤 {DEV_USERNAME}", supports_streaming=True)
            else: await query.message.reply_audio(audio=f, caption=f"🎵 {DEV_USERNAME}")
        
        # تحديث السجل والإحصائيات
        total_downloads_count += 1
        if user_id not in download_history: download_history[user_id] = []
        download_history[user_id].append(url)
        
        os.remove(file_path)
        await query.delete_message()
    except Exception as e:
        await query.message.reply_text("❌ خطأ في التحميل!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم! أرسل الرابط.")
        else: await query.answer("⚠️ اشترك أولاً!", show_alert=True)
        return
    try:
        mode, link_id = query.data.split('|')
        url = context.user_data.get(link_id)
        if url: await download_logic(query, context, url, mode)
    except: pass

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('history', show_history))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(CommandHandler('send', broadcast))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()
