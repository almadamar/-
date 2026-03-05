import os
import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# ---------------- [1] الإعدادات ----------------
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
CHANNEL_ID = -1003773995399
CHANNEL_LINK = "https://t.me/+nBVM5qNb2uphMzUy"
DOWNLOAD_DIR = 'downloads'

logging.basicConfig(level=logging.INFO)
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

# ---------------- [2] وظيفة التحقق ----------------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ---------------- [3] المحرك (720p MP4) ----------------
async def download_video(query, context, url, mode):
    msg = await query.edit_message_text("⏳ جاري التحميل (720p)...")
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-vcodec', 'libx264', '-acodec', 'aac'],
        'quiet': True,
    }
    if mode == 'aud':
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})

    try:
        path = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]) or yt_dlp.YoutubeDL(ydl_opts).prepare_filename(yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)))
        final_path = path if mode == 'vid' else os.path.splitext(path)[0] + '.mp3'
        
        with open(final_path, 'rb') as f:
            if mode == 'vid': await query.message.reply_video(f, caption="✅ تم بواسطة @AN_AZ22")
            else: await query.message.reply_audio(f, caption="✅ تم بواسطة @AN_AZ22")
        
        if os.path.exists(final_path): os.remove(final_path)
        await msg.delete()
    except:
        await msg.edit_text("❌ فشل التحميل.")

# ---------------- [4] الأوامر ومعالجة الرسائل ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if await is_subscribed(context.bot, uid):
        await update.message.reply_text("🚀 أرسل الرابط للتحميل المباشر (720p).")
    else:
        btn = [[InlineKeyboardButton("📢 اشترك هنا", url=CHANNEL_LINK)], [InlineKeyboardButton("✅ اشتركت", callback_data="check")]]
        await update.message.reply_text("⚠️ اشترك أولاً:", reply_markup=InlineKeyboardMarkup(btn))

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    if not await is_subscribed(context.bot, update.effective_user.id): return
    
    link_id = str(random.randint(100, 999))
    context.user_data[link_id] = url
    keys = [[InlineKeyboardButton("🎬 فيديو", callback_data=f"vid|{link_id}"), InlineKeyboardButton("🎵 صوت", callback_data=f"aud|{link_id}")]]
    await update.message.reply_text("اختر الصيغة:", reply_markup=InlineKeyboardMarkup(keys))

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check":
        if await is_subscribed(context.bot, query.from_user.id): await query.edit_message_text("✅ تم التحقق!")
    elif "|" in query.data:
        mode, lid = query.data.split("|")
        url = context.user_data.get(lid)
        if url: await download_video(query, context, url, mode)

# ---------------- [5] طريقة التشغيل الصحيحة لـ Render ----------------
def main():
    # استخدام الطريقة القياسية لتجنب AttributeError
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(cb))
    
    print("--- البوت يعمل الآن بنجاح (بدون نقاط) ---")
    
    # استخدام run_polling مباشرة وهي الطريقة المستقرة
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
