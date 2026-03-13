import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

# البيانات كما هي في كودك
OLD_CHANNEL_ID = "@UpGo2"
STORAGE_CHANNEL_ID = "@Musiciqh"
MAIN_LINK = "https://t.me/UpGo2"
STORAGE_LINK = "https://t.me/Musiciqh"
BOT_USERNAME = "AutoMusicHubBot"

SONG_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}],
    'outtmpl': 'temp/%(title)s.%(ext)s',
    'quiet': True,
}

async def on_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # الفلتر هنا سيلتقط أي رابط يبدأ بـ http
    if not url or not url.startswith("http"): return

    # نظام التحقق من الاشتراك
    try:
        member = await context.bot.get_chat_member(chat_id=OLD_CHANNEL_ID, user_id=update.effective_user.id)
        if member.status in ['left', 'kicked']:
            kb = [[InlineKeyboardButton("📢 اشترك في القناة الأساسية", url=MAIN_LINK)]]
            await update.message.reply_text("⚠️ يرجى الاشتراك أولاً:", reply_markup=InlineKeyboardMarkup(kb))
            return
    except: pass

    # عرض زر الأرشفة (سيعمل بجانب رسالة البوت القديم)
    kb = [[InlineKeyboardButton("🚀 بدء الأرشفة والترحيل لـ Musiciqh", callback_data=f"dl_{url}")]]
    await update.message.reply_text("📂 نظام الأرشفة جاهز لهذا الرابط:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith("dl_"): return
    await query.answer()
    # ... بقية دالة التحميل كما هي في كودك السابق ...

def setup_music_module(application):
    # وضعنا هذا في المجموعة 2 لضمان استلامه للرابط مع المجموعة 1 في وقت واحد
    application.add_handler(MessageHandler(filters.TEXT & filters.Entity("url"), on_link_received), group=2)
    application.add_handler(CallbackQueryHandler(on_button_click), group=2)
