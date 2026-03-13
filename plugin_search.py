import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes

# إعدادات البحث السريع
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
}

async def youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    
    # نتأكد أن الرسالة ليست رابطاً وليست أمراً (لأن الروابط لها ملحقاتها الخاصة)
    if query.startswith("http") or query.startswith("/"):
        return

    status = await update.message.reply_text(f"🔍 جاري البحث عن: {query}...")

    try:
        # البحث عن أول 5 نتائج
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']

        if not search_results:
            await status.edit_text("❌ لم يتم العثور على نتائج.")
            return

        keyboard = []
        for video in search_results:
            title = video.get('title', 'فيديو بدون عنوان')[:30] + "..."
            url = f"https://www.youtube.com/watch?v={video['id']}"
            # نضع زر لكل نتيجة يرسل الرابط للبوت مرة أخرى ليتم معالجته بملحق التحميل
            keyboard.append([InlineKeyboardButton(f"🎬 {title}", callback_data=f"none")])
            keyboard.append([
                InlineKeyboardButton("📥 تحميل فيديو", switch_inline_query_current_chat=url),
                InlineKeyboardButton("🎵 تحميل صوت", switch_inline_query_current_chat=url)
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await status.edit_text(f"✅ نتائج البحث عن: {query}\n\nإضغط على الرابط الذي يظهر لك ثم أرسله للتحميل:", reply_markup=reply_markup)

    except Exception as e:
        print(f"Search Error: {e}")
        await status.edit_text("⚠️ حدث خطأ أثناء البحث، جرب كلمة أخرى.")

def setup(app):
    # يعمل هذا المعالج فقط إذا لم تكن الرسالة رابطاً أو أمراً
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Entity("url"), youtube_search))
