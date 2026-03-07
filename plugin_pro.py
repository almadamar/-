import os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler

DB_FILE = "users.txt"
OWNER_ID = 162459553

def get_all_users():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f:
        return {int(line.strip()) for line in f if line.strip()}

async def kmr_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    
    users_count = len(get_all_users())
    keyboard = [
        [InlineKeyboardButton("📊 تحديث الإحصائيات", callback_data="refresh_stats")],
        [InlineKeyboardButton("📢 إرسال إذاعة (BC)", callback_data="start_bc")]
    ]
    
    await update.message.reply_text(
        f"🛠 **لوحة تحكم KMR**\n\n👥 المشتركون: `{users_count}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID: return
    
    # حماية: تجاهل أي بيانات لا تخص الإدارة (مثل أزرار التحميل)
    if "|" in query.data: return 
    
    await query.answer()
    if query.data == "refresh_stats":
        users_count = len(get_all_users())
        await query.edit_message_text(f"✅ تم التحديث!\n👥 المشتركون: `{users_count}`", 
                                      reply_markup=query.message.reply_markup, parse_mode='Markdown')

async def broadcast_ar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args: return
    msg_text = " ".join(context.args)
    users = get_all_users()
    for u_id in users:
        try:
            await context.bot.send_message(u_id, msg_text)
            await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text("✅ تمت الإذاعة.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'(?i)kmr|خدماتي'), kmr_panel))
    app.add_handler(CommandHandler("اذاعة", broadcast_ar))
    app.add_handler(CallbackQueryHandler(handle_admin_callbacks))
