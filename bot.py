import os
import logging
import asyncio
import datetime
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# --- [ الإعدادات ] ---
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'

# تهيئة المجلدات واللوق
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
logging.basicConfig(level=logging.INFO)

# قاعدة بيانات مؤقتة
active_users = set()

# --- [ ميزات الحماية واللغة ] ---
def get_user_lang(update: Update):
    return 'ar' if update.effective_user.language_code == 'ar' else 'en'

async def check_subscription(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- [ محرك التحميل الاحترافي ] ---
async def download_engine(query, context, url, mode):
    lang = get_user_lang(query)
    msg_wait = "⏳ جاري التحميل... يرجى الانتظار" if lang == 'ar' else "⏳ Downloading... Please wait"
    msg_status = await query.edit_message_text(msg_wait)
    
    # إعدادات مستوحاة من VAFBoT لتجاوز القيود
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'], # ترميز عالمي لعدم تجميد الفيديو
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }

    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        def run_ytdlp():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.wait_for(asyncio.to_thread(run_ytdlp), timeout=180)
        
        # التأكد من الصيغة النهائية
        final_file = file_path if mode == 'vid' else os.path.splitext(file_path)[0] + '.mp3'
        
        caption = "✅ تم التحميل بواسطة البوت الخاص بك" if lang == 'ar' else "✅ Downloaded by your bot"
        
        with open(final_file, 'rb') as f:
            if mode == 'vid':
                await query.message.reply_video(video=f, caption=caption, supports_streaming=True)
            else:
                await query.message.reply_audio(audio=f, caption=caption)

        if os.path.exists(final_file): os.remove(final_file)
        await msg_status.delete()
    except Exception as e:
        error_msg = "❌ فشل التحميل. الرابط قد يكون خاصاً." if lang == 'ar' else "❌ Download failed. Private link?"
        await msg_status.edit_text(error_msg)

# --- [ معالجة الرسائل ] ---
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    lang = get_user_lang(update)
    active_users.add(user_id)

    if not url.startswith("http"): return

    # فحص الاشتراك
    if not await check_subscription(context.bot, user_id):
        btn = [[InlineKeyboardButton("📢 Channel / القناة", url=CHANNEL_LINK)],
               [InlineKeyboardButton("✅ تم الاشتراك / Joined", callback_data="check_sub")]]
        return await update.message.reply_text("⚠️ اشترك أولاً لتتمكن من التحميل:", reply_markup=InlineKeyboardMarkup(btn))

    link_id = str(random.randint(1000, 9999))
    context.user_data[link_id] = url
    
    # واجهة اختيار الصيغة (مثل Allsavers)
    kb = [[InlineKeyboardButton("🎬 Video MP4 (720p)", callback_data=f'vid|{link_id}')],
          [InlineKeyboardButton("🎵 Audio MP3", callback_data=f'aud|{link_id}')]]
    
    txt = "⚙️ اختر الصيغة المطلوبة:" if lang == 'ar' else "⚙️ Select format:"
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    msg = "🚀 أرسل أي رابط (تيك توك، يوتيوب، إنستغرام، Pinterest) وسأحمله لك!" if lang == 'ar' else "🚀 Send any link to download!"
    await update.message.reply_text(msg)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text(f"📊 عدد المستخدمين: {len(active_users)}")

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('|')
    
    if data[0] == "check_sub":
        if await check_subscription(context.bot, query.from_user.id):
            await query.edit_message_text("✅ تم التفعيل! أرسل الرابط الآن.")
    elif len(data) == 2:
        url = context.user_data.get(data[1])
        if url: await download_engine(query, context, url, data[0])

# --- [ التشغيل ] ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.add_handler(CallbackQueryHandler(callback_query))
    
    print("--- البوت العملاق قيد التشغيل ---")
    app.run_polling()
