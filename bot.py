import os
import logging
import datetime
import asyncio
import requests
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
GEMINI_KEY = "ضع_مفتاح_جيمناي_هنا"

DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 50 * 1024 * 1024 
active_users = set()
user_languages = {} # لتخزين لغة كل مستخدم

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
logging.basicConfig(level=logging.INFO)

# ---------------- [2] نظام اللغات (الترجمة) ----------------
STRINGS = {
    'ar': {
        'start_msg': "🚀 **أهلاً بك في البوت الشامل!**\n\n🎬 يدعم: يوتيوب، تيك توك، فيسبوك، Pinterest\n✨ المزايا: تحميل فيديو/صوت، تلخيص AI\n\nأرسل الرابط الآن!",
        'sub_required': "⚠️ يجب عليك الاشتراك في القناة أولاً لتفعيل البوت:",
        'sub_btn': "📢 اشترك في القناة",
        'sub_done': "✅ تم الاشتراك، ابدأ",
        'wait': "⏳ انتظر قليلاً جاري فحص الرابط...",
        'options': "⚙️ اختر الإجراء المطلوب للرابط:",
        'vid_btn': "🎬 فيديو MP4",
        'aud_btn': "🎵 صوت MP3",
        'ai_btn': "📝 تلخيص بالذكاء الاصطناعي",
        'success': "✅ تم التحميل بنجاح بواسطة @AN_AZ22",
        'error': "❌ فشل التحميل، تأكد من الرابط."
    },
    'en': {
        'start_msg': "🚀 **Welcome to the Ultimate Bot!**\n\n🎬 Supports: YouTube, TikTok, FB, Pinterest\n✨ Features: Video/Audio download, AI Summary\n\nSend a link now!",
        'sub_required': "⚠️ You must subscribe to our channel first:",
        'sub_btn': "📢 Subscribe Now",
        'sub_done': "✅ Subscribed, Start",
        'wait': "⏳ Processing link, please wait...",
        'options': "⚙️ Select an action for the link:",
        'vid_btn': "🎬 Video MP4",
        'aud_btn': "🎵 Audio MP3",
        'ai_btn': "📝 AI Summary",
        'success': "✅ Downloaded successfully by @AN_AZ22",
        'error': "❌ Download failed. Check the link."
    }
}

# ---------------- [3] دوال المساعدة والتعرف على اللغة ----------------
def detect_language(update: Update):
    user_id = update.effective_user.id
    # إذا لم تكن اللغة محددة، نتحقق من لغة واجهة تليجرام للمستخدم
    if user_id not in user_languages:
        lang_code = update.effective_user.language_code
        user_languages[user_id] = 'ar' if lang_code == 'ar' else 'en'
    return user_languages[user_id]

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ---------------- [4] الأوامر ومعالجة الرسائل ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = detect_language(update)
    active_users.add(user_id)

    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(STRINGS[lang]['start_msg'], parse_mode='Markdown')
    else:
        keys = [[InlineKeyboardButton(STRINGS[lang]['sub_btn'], url=CHANNEL_LINK)],
                [InlineKeyboardButton(STRINGS[lang]['sub_done'], callback_data="check_sub")]]
        await update.message.reply_text(STRINGS[lang]['sub_required'], reply_markup=InlineKeyboardMarkup(keys))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    lang = detect_language(update)
    
    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, user_id): return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    
    keyboard = [
        [InlineKeyboardButton(STRINGS[lang]['vid_btn'], callback_data=f'vid|{link_id}'), 
         InlineKeyboardButton(STRINGS[lang]['aud_btn'], callback_data=f'aud|{link_id}')],
        [InlineKeyboardButton(STRINGS[lang]['ai_btn'], callback_data=f'sum|{link_id}')]
    ]
    await update.message.reply_text(STRINGS[lang]['options'], reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- [5] منطق التحميل والردود ----------------
async def download_logic(query, context, url, mode):
    lang = user_languages.get(query.from_user.id, 'en')
    msg = await query.edit_message_text(STRINGS[lang]['wait'])
    
    def run_ytdlp():
        ydl_opts = {'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s', 'quiet': True}
        if mode == 'vid': ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})
        else: ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    try:
        path = await asyncio.to_thread(run_ytdlp)
        with open(path, 'rb') as f:
            if mode == 'vid': await query.message.reply_video(video=f, caption=STRINGS[lang]['success'])
            else: await query.message.reply_audio(audio=f, caption=STRINGS[lang]['success'])
        os.remove(path)
        await msg.delete()
    except: await msg.edit_text(STRINGS[lang]['error'])

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = detect_language(update)
    await query.answer()
    
    data = query.data.split('|')
    if data[0] == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): 
            await query.edit_message_text("✅ Done / تم التفعيل")
    elif len(data) == 2:
        url = context.user_data.get(data[1])
        await download_logic(query, context, url, data[0])

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("--- MULTI-LANGUAGE BOT STARTED ---")
    app.run_polling()
