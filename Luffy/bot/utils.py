# bot/utils.py
import requests
from telegram import Bot
from asgiref.sync import sync_to_async  # Import sync_to_async

@sync_to_async
def stream_to_telegram(bot_token, chat_id, file_url, file_name):
    bot = Bot(token=bot_token)
    
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        bot.send_document(chat_id=chat_id, document=response.raw, filename=file_name)
    else:
        raise Exception("Failed to fetch the file.")
