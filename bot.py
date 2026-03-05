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
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (حد التليجرام القياسي للملفات)
COOLDOWN_SECONDS = 3 # تقليل وقت الانتظار لسرعة الاستجابة

# مخازن البيانات
active_users = set()
download_history = {}
total_downloads_count = 0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    
    msg = (
        "🔥 **مرحباً بك في النسخة الاحترافية!**\n\n"
        "✅ تم تحسين دعم فيسبوك، تيك توك، وإنستغرام.\n"
        "📜 عرض سجلك: /history\n"
        "📊 الإحصائيات: /stats (للمطور)\n"
        "🚀 أرسل الرابط الآن وسأقوم بالمعالجة فوراً."
    )

    if await is_subscribed(context.bot, user_id):
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        keyboard = [[InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("✅ تم الاشتراك، ابدأ", callback_data="check_sub")]]
        await update.message.reply_text("⚠️ البوت يعمل للمشتركين فقط:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = download_history.get(user_id, [])
    if not history:
        await update.message.reply_text("📭 لا توجد تحميلات سابقة.")
        return
    msg = "📜 **آخر روابط قمت بتحميلها:**\n\n" + "\n".join([f"🔗 {l}" for l in history[-5:]])
    await update.message.reply_text(msg, disable_web_page_preview=True, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(f"📊 **إحصائيات النظام:**\n\n👥 مستخدمين: {len(active_users)}\n📥 تحميلات ناجحة: {total_downloads_count}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❌ اكتب الرسالة بعد الأمر. مثال: /send هالو")
        return
    for uid in active_users:
        try: await context.bot.send_message(chat_id=uid, text=f"📢 **رسالة من الإدارة:**\n\n{text}", parse_mode='Markdown')
        except: continue
    await update.message.reply_text("✅ تم الإرسال للجميع.")

# ---------------- معالجة الرسائل ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active_users.add(user_id)
    url = update.message.text
    if not url.startswith("http"): return

    if not await is_subscribed(context.bot, user_id):
        await start(update, context)
        return

    allowed, wait = check_cooldown(user_id)
    if not allowed:
        await update.message.reply_text(f"⏳ انتظر {wait} ثانية.")
        return

    link_id = str(datetime.datetime.now().timestamp()).replace(".", "")
    context.user_data[link_id] = url
    
    keyboard = [
        [InlineKeyboardButton("🎬 تحميل فيديو MP4", callback_data=f'vid|{link_id}')],
        [InlineKeyboardButton("🎵 تحميل صوت MP3", callback_data=f'aud|{link_id}')]
    ]
    await update.message.reply_text("✅ تم استلام الرابط، اختر الصيغة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- منطق التحميل الاحترافي ----------------
async def download_logic(query, context, url, mode):
    global total_downloads_count
    user_id = query.from_user.id
    msg_status = await query.edit_message_text("🔍 جاري فحص الرابط وتجاوز الحماية...")

    def ytdlp_download():
        # إعدادات قوية لتجاوز حماية فيسبوك وتيك توك
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'socket_timeout': 30,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }
        
        if mode == 'vid':
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
        else:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if mode == 'vid':
                final = os.path.splitext(path)[0] + '.mp4'
                if os.path.exists(path) and path != final: os.rename(path, final)
                return final
            return os.path.splitext(path)[0] + '.mp3'

    try:
        # تنفيذ التحميل مع مهلة زمنية (Timeout) لمنع التجمد
        file_path = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(None, ytdlp_download),
            timeout=120  # دقيقتين كحد أقصى للتحميل
        )
        
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            await query.message.reply_text("❌ عذراً! حجم الفيديو يتجاوز 50MB، تليجرام لا يسمح للبوتات بإرسال ملفات ضخمة حالياً.")
        else:
            await msg_status.edit_text("📤 جاري الرفع إلى تليجرام...")
            with open(file_path, 'rb') as f:
                if mode == 'vid':
                    await query.message.reply_video(video=f, caption=f"✅ تم التحميل بنجاح\n👤 المطور: {DEV_USERNAME}", supports_streaming=True)
                else:
                    await query.message.reply_audio(audio=f, caption=f"🎵 تم التحويل بواسطة: {DEV_USERNAME}")
            
            total_downloads_count += 1
            if user_id not in download_history: download_history[user_id] = []
            download_history[user_id].append(url)

        if os.path.exists(file_path): os.remove(file_path)
        await msg_status.delete()

    except asyncio.TimeoutError:
        await msg_status.edit_text("⚠️ استغرق الرابط وقتاً طويلاً جداً (Timeout). قد يكون الرابط محمي أو السيرفر بطيء.")
    except Exception as e:
        logger.error(f"Download Error: {e}")
        await msg_status.edit_text("❌ فشل التحميل. تأكد أن الرابط عام (Public) وليس خاصاً.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التفعيل! أرسل رابطك الآن.")
        else: await query.answer("⚠️ لم تشترك بعد!", show_alert=True)
        return
    
    data = query.data.split('|')
    if len(data) == 2:
        mode, link_id = data
        url = context.user_data.get(link_id)
        if url: await download_logic(query, context, url, mode)
        else: await query.edit_message_text("❌ انتهت الجلسة. أرسل الرابط مرة أخرى.")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('history', show_history))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(CommandHandler('send', broadcast))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("--- PROFESSIONAL BOT STARTED ---")
    app.run_polling()
