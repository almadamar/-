import os, logging, glob, importlib, asyncio
from telegram.ext import Application

# --- [الإعدادات الثابتة] ---
TOKEN = "6099646606:AAHu-znvZ9bawGNl4autKn3YcMXSrxz4NzI"
OWNER_ID = 162459553
DB_FILE = "users.txt"
active_users = set()

logging.basicConfig(level=logging.INFO)

# تحميل قاعدة البيانات
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        for line in f:
            if line.strip(): active_users.add(int(line.strip()))

# وظيفة لتحميل الملحقات تلقائياً دون تعديل الكود الأساسي
def load_plugins(app):
    for f in glob.glob("plugin_*.py"):
        module_name = f[:-3]
        try:
            # إعادة تحميل الملحق إذا كان موجوداً أو تحميله لأول مرة
            m = importlib.import_module(module_name)
            importlib.reload(m)
            if hasattr(m, "setup"):
                m.setup(app)
                print(f"✅ تم تحميل الملحق: {module_name}")
        except Exception as e:
            print(f"❌ خطأ في الملحق {module_name}: {e}")

def main():
    # بناء التطبيق مع ميزة تنظيف الطلبات القديمة (حل الـ Conflict)
    app = Application.builder().token(TOKEN).build()
    
    # تحميل كافة الملحقات الموجودة في المجلد
    load_plugins(app)
    
    print("🚀 المحرك الأساسي يعمل... بانتظار الملحقات.")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
