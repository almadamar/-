import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK

async def direct_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http") or "youtube" in url or "youtu.be" in url: return
    
    bot_info = await context.bot.get_me()
    status = await update.message.reply_text("⏳ جاري التحميل... (تلقائي)")

    ydl_opts = {
        # الحل: يحاول 720p، فإذا فشل يأخذ أفضل جودة فيديو + صوت متاحة
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        def run():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        path = await asyncio.to_thread(run)
        
        caption = f"✅ تم التحميل بواسطة: @{bot_info.username}\n📢 القناة: {CHANNEL_LINK}"
        kb = [[InlineKeyboardButton("🚀 مشاركة البوت", switch_inline_query=f"@{bot_info.username}")],
              [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"to_mp3|{os.path.basename(path)}")]]

        with open(path, 'rb') as f:
            await update.message.reply_video(video=f, caption=caption, reply_markup=InlineKeyboardMarkup(kb), supports_streaming=True)
        
        await status.delete()
        if os.path.exists(path): os.remove(path)
    except:
        await status.edit_text("❌ عذراً، لم أتمكن من استخراج الفيديو من هذا الرابط.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl))
