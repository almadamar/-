import os, yt_dlp, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK

async def yt_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not any(x in url for x in ["youtube.com", "youtu.be"]): return
    
    bot_info = await context.bot.get_me()
    status = await update.message.reply_text("📺 جاري معالجة فيديو يوتيوب...")

    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
        'outtmpl': f'downloads/%(id)s.%(ext)s',
        'quiet': True
    }

    try:
        path = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).prepare_filename(yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True)))
        
        caption = f"🎬 يوتيوب بواسطة: @{bot_info.username}\n📢 {CHANNEL_LINK}"
        kb = [[InlineKeyboardButton("🚀 مشاركة", switch_inline_query=f"@{bot_info.username}")],
              [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"to_mp3|{os.path.basename(path)}")]]

        with open(path, 'rb') as f:
            await update.message.reply_video(video=f, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        
        await status.delete()
        if os.path.exists(path): os.remove(path)
    except:
        await status.edit_text("❌ فشل تحميل فيديو يوتيوب.")

def setup(app):
    app.add_handler(MessageHandler(filters.Regex(r'youtube|youtu\.be'), yt_direct))
