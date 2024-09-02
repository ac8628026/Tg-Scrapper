# import os
# import django
# django.setup()
# import logging
# import asyncio
# from dotenv import load_dotenv
# from channels.generic.websocket import AsyncWebsocketConsumer
# from telegram.ext import Application, CommandHandler
# from bot.tg_bot import start  # Ensure the correct import path

# load_dotenv()


# TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
# )
# logger = logging.getLogger(__name__)

# class TelegramConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         logger.info("WebSocket connection requested.")
#         await self.accept()
#         logger.info("WebSocket connection accepted.")
#         self.application = await self.setup_telegram_bot()

#     async def disconnect(self, close_code):
#         logger.info(f"WebSocket disconnected with close code: {close_code}")
#         await self.application.stop()
    
#     async def receive(self, text_data):
#         logger.info(f"Received message: {text_data}")

#     async def setup_telegram_bot(self):
#         application = Application.builder().token(TOKEN).build()

#         start_handler = CommandHandler('start', start)
#         application.add_handler(start_handler)

#         asyncio.create_task(application.start())

#         return application
