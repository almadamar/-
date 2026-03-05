import os
import logging
import datetime
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- إعدادات البوت ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"

DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 50 * 1024 * 1024
DEFAULT_POINTS = 15
REFERRAL_REWARD = 3

# مخازن البيانات
user_points = {}  
active_users = set()

logging.basicConfig(level=logging.INFO)

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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
    
    # نظام الإحالة (Referral)
    if context.args and context.args[0].isdigit():
        ref_id = int(context.args[0])
        if user_id not in user_points and ref_id != user_id:
            user_points[user_id] = DEFAULT_POINTS
            user_points[ref_id] = user_points.get(ref_id, 0) + REFERRAL_REWARD
            try: await context.bot.send_message(chat_id=ref_id, text=f"🎁 مبروك! انضم مستخدم جديد عبر رابطك وحصلت على {REFERRAL_REWARD} نقاط مكافأة.")
            except: pass

    if user_id not in user_points:
        user_points[user_id] = DEFAULT_POINTS

    welcome = (f"🚀 **أهلاً بك في بوت التحميل المطور!**\n\n"
               f"💰 رصيدك الحالي: {user_points[user_id]} نقطة\n"
               f"🔗 رابط الدعوة الخاص بك لزيادة النقاط:\n"
               f"`https://t.me/{bot_info.username}?start={user_id}`\n\n"
               f"📢 قناتنا: {CHANNEL_LINK}\n\n"
               f"أرسل رابط الفيديو أو الملف المباشر للتحميل فوراً.")
    
    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(welcome, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        keys = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ تم الاشتراك، ابدأ الآن", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ عذراً، يجب الاشتراك في القناة أولاً لتفعيل البوت:", reply_markup=InlineKeyboardMarkup(keys))

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    points = user_points.get(user_id, 0)
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    await update.message.reply_text(f"👤 **معلومات حسابك:**\n\n💰 النقاط: {points}\n🔗 رابطك: `{ref_link}`", parse_mode='Markdown')

# ---------------- معالجة الرسائل ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    if not url.startswith("http"): return

    if not await is_subscribed(context.bot, user_id):
        await start(update, context)
        return

    if user_points.get(user_id, 0) <= 0:
        await update.message.reply_text("❌ نفذت نقاطك! قم بمشاركة البوت مع أصدقائك للحصول على نقاط إضافية.")
        return

    direct_exts = ('.zip', '.pdf', '.mp4', '.jpg', '.apk', '.exe', '.mp3')
    if any(url.lower().endswith(ext) for ext in direct_exts):
        await download_direct(update, context, url)
        return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو MP4", callback_data=f'vid|{link_id}')],
            [InlineKeyboardButton("🎵 صوت MP3", callback_data=f'aud|{link_id}')]]
    await update.message.reply_text(f"💰 الرصيد المتاح: {user_points[user_id]}\nاختر الصيغة المطلوبة:", reply_markup=InlineKeyboardMarkup(keys))

# ---------------- التحميل المباشر (مع الوصف) ----------------
async def download_direct(update, context, url):
    user_id = update.effective_user.id
    bot_info = await context.bot.get_me()
    status = await update.message.reply_text("⏳ جاري سحب الملف المباشر...")
    try:
        file_name = f"{DOWNLOAD_DIR}/file_{user_id}_" + url.split('/')[-1].split('?')[0]
        r = requests.get(url, stream=True, timeout=120)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        
        caption = f"✅ تم تحميل الملف بنجاح\n\n🤖 البوت: @{bot_info.username}\n📢 القناة: {CHANNEL_LINK}"
        
        with open(file_name, 'rb') as f:
            await update.message.reply_document(document=f, caption=caption)
        
        os.remove(file_name)
        user_points[user_id] -= 1
        await status.delete()
    except: await status.edit_text("❌ فشل تحميل الملف.")

# ---------------- التحميل من المنصات (مع الوصف) ----------------
async def download_logic(query, context, url, mode):
    user_id = query.from_user.id
    bot_info = await context.bot.get_me()
    msg_status = await query.edit_message_text("⏳ جاري التحميل... يرجى الانتظار.")

    def ytdlp_process():
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }
        if mode == 'vid':
            ydl_opts.update({'format': 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
        else:
            ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            final = os.path.splitext(path)[0] + ('.mp4' if mode == 'vid' else '.mp3')
            if os.path.exists(path) and path != final: os.rename(path, final)
            return final

    try:
        path = await asyncio.wait_for(asyncio.get_running_loop().run_in_executor(None, ytdlp_process), timeout=180)
        
        # الوصف الذي سيظهر أسفل الفيديو
        caption = (f"✅ تم التحميل بنجاح!\n\n"
                   f"🤖 البوت: @{bot_info.username}\n"
                   f"📢 القناة: {CHANNEL_LINK}\n"
                   f"🎁 اربح نقاط مجانية: https://t.me/{bot_info.username}?start={user_id}")
        
        with open(path, 'rb') as f:
            if mode == 'vid': 
                await query.message.reply_video(video=f, caption=caption, supports_streaming=True)
            else: 
                await query.message.reply_audio(audio=f, caption=caption)
        
        user_points[user_id] -= 1
        if os.path.exists(path): os.remove(path)
        await msg_status.delete()
    except Exception:
        await msg_status.edit_text("❌ فشل التحميل.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التفعيل! أرسل رابطك.")
        else: await query.answer("⚠️ لم تشترك بعد!", show_alert=True)
        return
    
    data = query.data.split('|')
    if len(data) == 2:
        url = context.user_data.get(data[1])
        if url: await download_logic(query, context, url, data[0])

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('me', me))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling()
