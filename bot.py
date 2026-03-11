import os, importlib, asyncio
from telegram.ext import ApplicationBuilder
from config_data import TOKEN, DOWNLOAD_DIR

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

async def post_init(application):
    plugins = ['plugin_pro', 'plugin_youtube', 'plugin_audio', 'plugin_extras']
    for plugin in plugins:
        try:
            module = importlib.import_module(plugin)
            module.setup(application)
            print(f"✅ Active: {plugin}")
        except Exception as e:
            print(f"❌ Error {plugin}: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    print("--- BOT IS STARTING ---")
    app.run_polling()
