import os
import logging
import datetime
import asyncio
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- [1] الإعدادات الأساسية ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
DEV_USERNAME = "@AN_AZ22"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
GEMINI_KEY = "ضع_مفتاح_جيمناي_هنا" # اختياري للتلخيص

DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 50 * 1024 * 1024 
COOLDOWN_SECONDS = 3

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
logging.basicConfig(level=logging.INFO)

# ذاكرة البوت
user_languages = {}
download_history = {}
user_cooldown = {}

# ---------------- [2] قاموس اللغات الموحد ----------------
STRINGS = {
    'ar': {
        'start': "🚀 **مرحباً بك في البوت الشامل!**\n\n🎬 يدعم: YouTube, TikTok, Pinterest, FB, Insta\n✅ الجودة: 720p MP4 (تعمل على جميع الأجهزة)\n✨ المزايا: تحميل، تلخيص AI، سجل.\n\nأرسل الرابط الآن!",
        'sub_req': "⚠️ يجب الاشتراك في القناة أولاً لتفعيل البوت:",
        'sub_btn': "📢 اشترك في القناة",
        'sub_done': "✅ تم الاشتراك، ابدأ",
        'wait': "⏳ جاري المعالجة بدقة 720p (يرجى الانتظار)...",
        'options': "⚙️ اختر الإجراء المطلوب:",
        'vid_btn': "🎬 فيديو MP4",
        'aud_btn': "🎵 صوت MP3",
        'ai_btn': "📝 تلخيص بالذكاء الاصطناعي",
        'success': f"✅ تم التحميل بنجاح\n👤 المطور: {DEV_USERNAME}",
        'error': "❌ فشل التحميل. تأكد من الرابط أو حاول لاحقاً.",
        'cooldown': "⏳ يرجى الانتظار {} ثانية بين الطلبات."
    },
    'en': {
        'start': "🚀 **Welcome to the Ultimate Bot!**\n\n🎬 Supports: YouTube, TikTok, Pinterest, FB, Insta\n✅ Quality: 720p MP4 (Works on all devices)\n✨ Features: Download, AI Summary, History.\n\nSend a link now!",
        'sub_req': "⚠️ Please subscribe to our channel first:",
        'sub_btn': "📢 Subscribe Now",
        'sub_done': "✅ Subscribed, Start",
        'wait': "⏳ Processing in 720p (Please wait)...",
        'options': "⚙️ Select an action:",
        'vid_btn': "🎬 Video MP4",
        'aud_btn': "🎵 Audio MP3",
        'ai_btn': "📝 AI Summary",
        'success': f"✅ Downloaded successfully\n👤 Dev: {DEV_USERNAME}",
        'error': "❌ Download failed. Check link or try again.",
        'cooldown': "⏳ Please wait {}s between requests."
    }
}

# ---------------- [3] دوال الحماية واللغة ----------------
def get_lang(update: Update):
    uid = update.effective_user.id
    if uid not in user_languages:
        lang_code = update.effective_user.language_code
        user_languages[uid] = 'ar' if lang_code == 'ar' else 'en'
    return user_languages[uid]

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

def check_cooldown(user_id):
    now = datetime.datetime.now()
    if user_id in user_cooldown:
        diff = (now - user_cooldown[user_id]).total_seconds()
        if diff < COOLDOWN_SECONDS: return False, int(COOLDOWN_SECONDS - diff)
    user_cooldown[user_id] = now
    return True, 0

# ---------------- [4] المحرك الرئيسي (720p MP4 للجميع) ----------------
async def download_logic(query, context, url, mode):
    lang = get_lang(query)
    msg_status = await query.edit_message_text(STRINGS[lang]['wait'])
    
    ydl_opts = {
        # توحيد الصيغة والدقة لجميع المواقع بما فيها Pinterest
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'], # حل مشكلة الشاشة السوداء
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.wait_for(asyncio.to_thread(run_dl), timeout=200)
        
        # تصحيح الامتداد يدوياً إذا لزم الأمر
        final_file = file_path if mode == 'vid' else os.path.splitext(file_path)[0] + '.mp3'
        if not os.path.exists(final_file) and os.path.exists(os.path.splitext(file_path)[0] + '.mp4'):
            final_file = os.path.splitext(file_path)[0] + '.mp4'

        with open(final_file, 'rb') as f:
            if mode == 'vid':
                await query.message.reply_video(video=f, caption=STRINGS[lang]['success'], supports_streaming=True)
            else:
                await query.message.reply_audio(audio=f, caption=STRINGS[lang]['success'])
        
        # إضافة للسجل
        uid = query.from_user.id
        if uid not in download_history: download_history[uid] = []
        download_history[uid].append(url)

        if os.path.exists(final_file): os.remove(final_file)
        await msg_status.delete()
    except Exception as e:
        print(f"Error: {e}")
        await msg_status.edit_text(STRINGS[lang]['error'])

# ---------------- [5] معالجة الرسائل والأوامر ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    lang = get_lang(update)

    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, user_id):
        keys = [[InlineKeyboardButton(STRINGS[lang]['sub_btn'], url=CHANNEL_LINK)],
                [InlineKeyboardButton(STRINGS[lang]['sub_done'], callback_data="check_sub")]]
        return await update.message.reply_text(STRINGS[lang]['sub_req'], reply_markup=InlineKeyboardMarkup(keys))

    allowed, wait = check_cooldown(user_id)
    if not allowed: return await update.message.reply_text(STRINGS[lang]['cooldown'].format(wait))

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    
    keys = [
        [InlineKeyboardButton(STRINGS[lang]['vid_btn'], callback_data=f'vid|{link_id}'),
         InlineKeyboardButton(STRINGS[lang]['aud_btn'], callback_data=f'aud|{link_id}')],
        [InlineKeyboardButton(STRINGS[lang]['ai_btn'], callback_data=f'sum|{link_id}')]
    ]
    await update.message.reply_text(STRINGS[lang]['options'], reply_markup=InlineKeyboardMarkup(keys))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(STRINGS[lang]['start'], parse_mode='Markdown')

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    data = query.data.split('|')

    if data[0] == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.edit_message_text("✅ Verified / تم التحقق")
    elif len(data) == 2:
        mode, link_id = data
        url = context.user_data.get(link_id)
        if mode in ['vid', 'aud']:
            await download_logic(query, context, url, mode)
        elif mode == 'sum':
            try:
                client = genai.Client(api_key=GEMINI_KEY)
                res = client.models.generate_content(model="gemini-3-flash-preview", contents=f"Summary for: {url}")
                await query.message.reply_text(f"📝 AI Summary:\n\n{res.text}")
            except: await query.message.reply_text("⚠️ AI feature not configured.")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- ALL-IN-ONE BOT IS ONLINE (720p MP4) ---")
    app.run_polling()
