import os
import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- [1] الإعدادات ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553 
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'

active_users = set()

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# ---------------- [2] وظيفة التحقق من الاشتراك ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ---------------- [3] محرك التحميل (720p MP4) ----------------
async def download_video(query, context, url, mode):
    msg = await query.edit_message_text("⏳ جاري التحميل بدقة 720p... يرجى الانتظار")
    
    ydl_opts = {
        # إعدادات ثابتة لجميع المنصات لضمان دقة 720p وصيغة MP4
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'], # ترميز منع الشاشة السوداء
        'quiet': True,
        'no_warnings': True
    }
    
    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        def dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        path = await asyncio.to_thread(dl)
        final_path = path if mode == 'vid' else os.path.splitext(path)[0] + '.mp3'

        with open(final_path, 'rb') as f:
            caption = "✅ تم التحميل بنجاح بواسطة @AN_AZ22"
            if mode == 'vid': 
                await query.message.reply_video(f, caption=caption, supports_streaming=True)
            else: 
                await query.message.reply_audio(f, caption=caption)
        
        if os.path.exists(final_path): os.remove(final_path)
        await msg.delete()
    except Exception as e:
        logging.error(f"Download Error: {e}")
        await msg.edit_text("❌ فشل التحميل. تأكد من الرابط أو حاول مرة أخرى.")

# ---------------- [4] الأوامر ومعالجة الرسائل ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    active_users.add(uid)
    
    welcome_msg = "🚀 **أهلاً بك في بوت التحميل الشامل!**\n\nالتحميل الآن **مجاني وغير محدود**.\nأرسل أي رابط (تيك توك، يوتيوب، إنستغرام، بنترست) وسأقوم بتحميله لك بدقة 720p."
    
    if await is_subscribed(context.bot, uid):
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    else:
        btn = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)], 
               [InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ **يجب عليك الاشتراك في القناة أولاً لتتمكن من استخدام البوت:**", 
                                      reply_markup=InlineKeyboardMarkup(btn), parse_mode='Markdown')

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    
    if not url.startswith("http"): return
    
    # فحص الاشتراك الإجباري
    if not await is_subscribed(context.bot, user_id):
        btn = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)], 
               [InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_sub")]]
        return await update.message.reply_text("⚠️ اشترك أولاً لتتمكن من التحميل:", reply_markup=InlineKeyboardMarkup(btn))

    link_id = str(random.randint(1000, 9999))
    context.user_data[link_id] = url
    
    keys = [[InlineKeyboardButton("🎬 فيديو MP4 (720p)", callback_data=f"vid|{link_id}"), 
             InlineKeyboardButton("🎵 صوت MP3", callback_data=f"aud|{link_id}")]]
    
    await update.message.reply_text("⚙️ **اختر الصيغة المطلوبة:**", reply_markup=InlineKeyboardMarkup(keys), parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.edit_message_text("✅ تم التحقق! يمكنك الآن إرسال الروابط والتحميل مجاناً.")
    elif "|" in query.data:
        mode, lid = query.data.split("|")
        url = context.user_data.get(lid)
        if url: 
            await download_video(query, context, url, mode)

# ---------------- [5] تشغيل البوت ----------------
async def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- البوت يعمل الآن بنجاح (بدون نقاط) ---")
    
    async with app:
        await app.initialize()
        await app.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
