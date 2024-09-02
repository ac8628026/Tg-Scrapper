import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Luffy.settings')
django.setup()

from telegram import Bot
from telegram.ext import Updater
from dotenv import load_dotenv
from bot.tg_bot import setup_dispatcher
# from tgbot.dispatcher import main

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
#

def run_polling(tg_token: str = TELEGRAM_TOKEN):
    """ Run bot in polling mode """
    application = Application.builder().token(tg_token).build()
    application = setup_dispatcher(application)


    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    run_polling()
    pass

# run_polling()