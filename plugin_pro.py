import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes, CallbackQueryHandler

OWNER_ID = 162459553
DB_FILE = "users.txt"

async def kmr_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    with open(DB_FILE, "r") as f: count = len(f.read().splitlines())
    
    kb = [[InlineKeyboardButton("📊 تحديث الإحصائيات", callback_data="adm_ref")],
          [InlineKeyboardButton("📂 نسخة احتياطية (Users)", callback_data="adm_bak")]]
    
    await update.message.reply_text(f"🛠 **لوحة تحكم KMR**\n\n👤 المطور: أنمار\n👥 المشتركين: `{count}`", 
                                  reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != OWNER_ID or "|" in query.data: return
    await query.answer()
    if query.data == "adm_ref":
        with open(DB_FILE, "r") as f: count = len(f.read().splitlines())
        await query.edit_message_text(f"✅ تم التحديث!\n👥 المشتركين: `{count}`", reply_markup=query.message.reply_markup)
    elif query.data == "adm_bak":
        await query.message.reply_document(document=open(DB_FILE, 'rb'), caption="💾 ملف مستخدميك.")

def setup(app):
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'(?i)^kmr$'), kmr_panel))
    app.add_handler(CallbackQueryHandler(handle_admin))
