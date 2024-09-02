# create a telegram bot which asks the user for the anime name and then returns the result from the fetch_anime_search_results() function in scraper.py

import logging
import os
import asyncio  # Add this line to import asyncio
from telegram import Update, Bot
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler,ConversationHandler,Updater,MessageHandler,filters,CallbackContext
from .scraper import *
print(os.getcwd())



logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

ANIME_NAME, ANIME_SELECTION, EPISODE_SELECTION = range(3)

async def start(update: Update, context: CallbackContext) -> None:
    # update.message.reply_text('Hi! Send me the name of an anime you want to search for.')
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="HELLOOOOOOOOOOOOOOOOOOOOOOOOO!!!!!!!"
    )
    return ANIME_NAME

async def anime_search(update: Update, context: CallbackContext) -> int:
    anime_name = update.message.text
    results = fetch_anime_search_results(anime_name)
    if results:
        context.user_data['anime_results'] = results
        reply_keyboard = [[result[1]] for result in results]  # Display titles only
        await update.message.reply_text(
            "Select an anime:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        print("Anime search results fetched")
        return ANIME_SELECTION
    else:
        await update.message.reply_text(f"No anime found for '{anime_name}'. Try another name.")
        print("No anime found")
        return ANIME_NAME

async def anime_selection(update: Update, context: CallbackContext) -> int:
    selected_anime = update.message.text
    results = context.user_data['anime_results']
    anime_url = next((result[0] for result in results if result[1] == selected_anime), None)
    if anime_url:
        context.user_data['selected_anime_url'] = anime_url
        seasons = fetch_anime_details(anime_url)
        if seasons:
            context.user_data['seasons'] = seasons
            reply_keyboard = [[season[1]] for season in seasons]
            await update.message.reply_text(
                "Select a season:",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            )
            print("Anime details fetched")
            return EPISODE_SELECTION
        else:
            await update.message.reply_text(f"No seasons found for '{selected_anime}'.")
            print("No seasons found")
            return ANIME_NAME
    else:
        await update.message.reply_text(f"Anime '{selected_anime}' not found in search results.")
        print("Anime not found in search results")
        return ANIME_NAME

async def episode_selection(update: Update, context: CallbackContext) -> int:
    selected_episode = update.message.text
    seasons = context.user_data['seasons']
    episode_url = next((season[0] for season in seasons if season[1] == selected_episode), None)
    if episode_url:
        file_data = await download_anime(episode_url)
        if file_data:
            # print("Downloaded file data")
            # file_like_object = io.BytesIO(file_data)
            # file_like_object.name = f"{selected_episode}.mp4"
            await update.message.reply_document(document=file_data, filename=f"{selected_episode}.mp4",read_timeout=600,write_timeout=600,connect_timeout=600)
            print("Sent file")
        else:
            await update.message.reply_text(f"Failed to find download link for '{selected_episode}'.")
            print("Failed to find download link")
    else:
        await update.message.reply_text(f"Episode '{selected_episode}' not found.")
        print("Episode not found")
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def setup_dispatcher(dp):
    # dp.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ANIME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_search)],
            ANIME_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_selection)],
            EPISODE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, episode_selection)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dp.add_handler(conv_handler)
    return dp           

# def main() -> None:
#     # Create the Updater and pass it your bot's token.
#     bot = Bot(token=TOKEN)
#     application = Application.builder().token(TOKEN).build()
#     conv_handler = ConversationHandler(
#         entry_points=[CommandHandler('start', start)],
#         states={
#             ANIME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_search)],
#             ANIME_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, anime_selection)],
#             EPISODE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, episode_selection)],
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     application.add_handler(conv_handler)
#     application.run_polling()


# if __name__ == '__main__':
#     main()  