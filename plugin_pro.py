import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK

async def direct_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http") or "youtube" in url or "youtu.be" in url: return
    
    bot_info = await context.bot.get_me()
    status = await update.message.reply_text("⏳ جاري محاولة كسر الحماية والتحميل...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        # إضافة رؤوس طلبات قوية لتجاوز حظر انستقرام
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.instagram.com/',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }

    try:
        def run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # محاولة استخراج الرابط المباشر أولاً
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        path = await asyncio.to_thread(run)
        
        caption = f"✅ تم التحميل بنجاح!\n🤖 @{bot_info.username}\n📢 {CHANNEL_LINK}"
        kb = [[InlineKeyboardButton("🚀 مشاركة البوت", switch_inline_query=f"@{bot_info.username}")]]

        with open(path, 'rb') as f:
            await update.message.reply_video(video=f, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        
        await status.delete()
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        # إذا فشل التحميل المباشر بسبب الحظر
        await status.edit_text("❌ انستقرام يفرض قيوداً حالياً على السيرفر.\nجرب إرسال الرابط مرة أخرى بعد دقيقة.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl))
