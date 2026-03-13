import os, yt_dlp, asyncio, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
from config_data import CHANNEL_LINK

async def direct_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # تجاهل الروابط الفارغة أو روابط يوتيوب (لأن لها ملحق خاص)
    if not url or not url.startswith("http") or "youtube" in url or "youtu.be" in url:
        return
    
    status = await update.message.reply_text("⏳ جاري التحميل...")
    # إنشاء معرف فريد للعملية
    t_id = f"soc_{random.randint(100, 999)}"
    context.user_data[t_id] = url

    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # تنفيذ التحميل في خيط منفصل لتجنب تعليق البوت
        info = await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        
        # --- الأزرار تظهر هنا فقط عند نجاح التحميل ---
        kb = [
            [InlineKeyboardButton("🚀 مشاركة", switch_inline_query=f"@{context.bot.username}")],
            [InlineKeyboardButton("🎵 تحويل لـ MP3", callback_data=f"sa|{t_id}")]
        ]

        with open(path, 'rb') as f:
            await update.message.reply_video(
                video=f, 
                caption=f"✅ تم التحميل بنجاح\n📢 {CHANNEL_LINK}", 
                reply_markup=InlineKeyboardMarkup(kb)
            )
        
        await status.delete()
        if os.path.exists(path): os.remove(path)

    except Exception as e:
        print(f"Pro DL Error: {e}")
        # رسالة بسيطة بدون أزرار عند الفشل
        await status.edit_text("❌ عذراً، فشل تحميل الفيديو. تأكد من أن الرابط عام أو جرب لاحقاً.")

def setup(app):
    # وضعنا أولوية عادية (بدون تحديد جروب) ليعمل بعد المراقبة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_dl))
