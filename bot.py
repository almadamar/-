import os
import logging
import datetime
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- إعدادات ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
DEV_USERNAME = "@AN_AZ22"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 52428800  # 50 MB
COOLDOWN_SECONDS = 5

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
    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(f"🚀 أرسل رابط الفيديو للتحميل بصيغة MP4 المتوافقة.\nالمطور: {DEV_USERNAME}")
    else:
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ تم الاشتراك، ابدأ الآن", callback_data="check_sub")]
        ]
        await update.message.reply_text("⚠️ يجب الاشتراك في القناة أولاً لاستخدام البوت!", 
                                      reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, url = update.effective_user, update.message.text
    if not url.startswith("http"): return

    if not await is_subscribed(context.bot, user.id):
        await start(update, context)
        return

    allowed, wait_time = check_cooldown(user.id)
    if not allowed:
        await update.message.reply_text(f"⏳ انتظر {wait_time} ثواني.")
        return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url

    keys = [
        [InlineKeyboardButton("🎬 فيديو MP4 (متوافق)", callback_data=f'vid_high|{link_id}')],
        [InlineKeyboardButton("🎵 ملف صوتي MP3", callback_data=f'aud|{link_id}')]
    ]
    await update.message.reply_text("📥 اختر ما تريد تحميله:", reply_markup=InlineKeyboardMarkup(keys))

# ---------------- منطق التحميل والترميم ----------------
async def download_logic(query, context, url, mode):
    await query.edit_message_text("⏳ جاري التحميل والمعالجة بصيغة متوافقة... يرجى الانتظار.")
    loop = asyncio.get_running_loop()

    def ytdlp_download():
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        if mode.startswith('vid'):
            ydl_opts.update({
                'format': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
        else:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if mode.startswith('vid'):
                base = os.path.splitext(filename)[0]
                final_name = base + '.mp4'
                if os.path.exists(filename) and filename != final_name:
                    if os.path.exists(final_name): os.remove(final_name)
                    os.rename(filename, final_name)
                return final_name
            else:
                return os.path.splitext(filename)[0] + '.mp3'

    try:
        file_path = await loop.run_in_executor(None, ytdlp_download)

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await query.message.reply_text("❌ الملف حجمه أكبر من 50MB (حدود تليجرام).")
            os.remove(file_path)
            return

        with open(file_path, 'rb') as f:
            if mode.startswith('vid'):
                await query.message.reply_video(video=f, caption=f"✅ تم التحميل بنجاح\n👤 بواسطة: {DEV_USERNAME}", supports_streaming=True)
            else:
                await query.message.reply_audio(audio=f, caption=f"🎵 بواسطة: {DEV_USERNAME}")

        os.remove(file_path)
        await query.delete_message()

    except Exception as e:
        logging.error(f"Error: {e}")
        await query.message.reply_text("❌ حدث خطأ! الرابط قد يكون غير مدعوم أو محمي.")

# ---------------- الأزرار ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.edit_message_text("✅ شكراً لاشتراكك! أرسل الرابط الآن.")
        else:
            await query.answer("⚠️ لم تشترك بعد في القناة!", show_alert=True)
        return

    try:
        mode, link_id = query.data.split('|')
        url = context.user_data.get(link_id)
        if not url:
            await query.edit_message_text("❌ انتهت الجلسة، أرسل الرابط مرة أخرى.")
            return
        await download_logic(query, context, url, mode)
    except:
        pass

# ---------------- التشغيل ----------------
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- BOT STARTED: MP4 COMPATIBILITY MODE ---")
    app.run_polling()
