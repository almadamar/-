import os
import logging
import asyncio
import random
import importlib
import glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# --- [الإعدادات] ---
OWNER_ID = 162459553 
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'
DB_FILE = "users.txt"

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

active_users = set()
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                if line.strip(): active_users.add(int(line.strip()))

def save_user(uid):
    if uid not in active_users:
        active_users.add(uid)
        with open(DB_FILE, "a") as f: f.write(f"{uid}\n")

load_db()

async def is_subscribed(bot, user_id):
    if user_id == OWNER_ID: return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- [المعالجات] ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)
    if await is_subscribed(context.bot, uid):
        msg = "🚀 أهلاً بك في بوت التحميل الشامل.\nأرسل الرابط مباشرة للبدء."
        if uid == OWNER_ID: msg += "\n\n🛠 المطور: /stats | /broadcast"
        await update.message.reply_text(msg)
    else:
        btn = [[InlineKeyboardButton("📢 انضم للقناة", url=CHANNEL_LINK)], [InlineKeyboardButton("✅ تأكيد الاشتراك", callback_data="check")]]
        await update.message.reply_text("⚠️ يرجى الاشتراك في القناة أولاً لاستخدام البوت.", reply_markup=InlineKeyboardMarkup(btn))

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context.bot, update.effective_user.id):
        await update.message.reply_text("❌ اشترك في القناة أولاً.")
        return
    text = update.message.text
    if not (text.startswith("http") or text.startswith("www")): return
    
    lid = str(random.randint(1000, 9999))
    context.user_data[lid] = text
    keys = [[
        InlineKeyboardButton("🎬 فيديو", callback_data=f"vid|{lid}"),
        InlineKeyboardButton("🎵 صوت", callback_data=f"aud|{lid}")
    ]]
    await update.message.reply_text("اختر الصيغة المطلوبة:", reply_markup=InlineKeyboardMarkup(keys))

async def download_video(query, context, url, mode):
    msg = await query.edit_message_text("⏳ جاري معالجة الرابط والتحميل...")
    
    # إعدادات محسنة للعمل بدون FFmpeg خارجي ولتوفير الذاكرة
    ydl_opts = {
        'format': 'best[ext=mp4]/best', # تحميل ملف مدمج جاهز
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'impersonate': 'chrome',
        'max_filesize': 50 * 1024 * 1024, # حد أقصى 50 ميجا لضمان استقرار السيرفر المجاني
    }
    
    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best'})

    try:
        # تنفيذ التحميل في خيط منفصل لمنع تجميد البوت
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        # التأكد من وجود الملف قبل الإرسال
        if not os.path.exists(file_path):
            raise Exception("الملف لم يحفظ بشكل صحيح على السيرفر.")

        caption = "✅ تم التحميل بنجاح بواسطة @Down2024_bot"
        
        with open(file_path, 'rb') as f:
            if mode == 'vid':
                await query.message.reply_video(video=f, caption=caption)
            else:
                await query.message.reply_audio(audio=f, caption=caption)
        
        # تنظيف الملفات بعد الإرسال لتوفير المساحة
        if os.path.exists(file_path):
            os.remove(file_path)
        await msg.delete()

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Download Error: {error_msg}")
        # رسالة خطأ ذكية تخبرك بالسبب في السجلات
        await msg.edit_text(f"❌ فشل التحميل.\nالسبب: {error_msg[:100]}")

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    
    if query.data == "check":
        if await is_subscribed(context.bot, uid):
            await query.edit_message_text("✅ تم تأكيد الاشتراك، يمكنك الآن إرسال الروابط.")
        else:
            await query.answer("⚠️ يجب عليك الانضمام للقناة أولاً!", show_alert=True)
            
    elif "|" in query.data:
        mode, lid = query.data.split("|")
        url = context.user_data.get(lid)
        if url:
            await download_video(query, context, url, mode)
        else:
            await query.edit_message_text("⚠️ انتهت صلاحية الرابط، يرجى إرساله مرة أخرى.")

def main():
    # بناء التطبيق مع ضبط إعدادات الاستقرار لـ Render
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(cb))
    
    print("🚀 البوت متصل الآن وجاهز للعمل...")
    # استخدام drop_pending_updates لتجنب الـ Conflict عند إعادة التشغيل
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
