# bot/views.py
import json
import asyncio
import logging
import os
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest,HttpResponseServerError, StreamingHttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from dotenv import load_dotenv
from django.views.decorators.http import require_GET
from telegram import Update, Bot
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ApplicationBuilder
from telegram.ext import Application
from telegram.ext import ConversationHandler
from .scraper import *
from .tg_bot import *
from bot.tasks import run_telegram_bot
from asgiref.sync import sync_to_async
# Load environment variables
load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

logger = logging.getLogger(__name__)


@require_GET
def anime_download_link(request):
    anime_name = request.GET.get('anime_name', None)
    if not anime_name:
        return HttpResponseBadRequest("Parameter 'anime_name' is required.")
    try:
        #extract title and link from the fetch_anime_search_results and return all the title and link
        link = fetch_anime_search_results(anime_name)
        if link:
            return JsonResponse({"anime_name": anime_name, "download_link": link})
        else:
            return JsonResponse({"error": f"No anime or episodes found for '{anime_name}'"}, status=404)
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {str(e)}")

@require_GET
def anime_season_details(request):
    anime_url = request.GET.get('anime_url', None)
    if not anime_url:
        return HttpResponseBadRequest("Parameter 'anime_url' is required.")
    try:
        #extract title and link from the fetch_anime_search_results and return all the title and link
        seasons = fetch_anime_details(anime_url)
        if seasons:
            return JsonResponse({"anime_url": anime_url, "seasons": seasons})
        else:
            return JsonResponse({"error": f"No seasons found for '{anime_url}'"}, status=404)
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {str(e)}")

@require_GET
def episode_link(request):
    episode_url = request.GET.get('episode_url', None)
    if not episode_url:
        return HttpResponseBadRequest("Parameter 'episode_url' is required.")
    try:
        #extract title and link from the fetch_anime_search_results and return all the title and link
        link = download_anime(episode_url)
        if link:
            return JsonResponse({"episode_url": episode_url, "download_link": link})
        else:
            return JsonResponse({"error": f"No download link found for '{episode_url}'"}, status=404)
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {str(e)}")
    
@require_GET
def episode(request):
    file_name = request.GET.get('file_name', None)
    if not file_name:
        return HttpResponseBadRequest("Parameter 'file_name' is required.")
    try:
        file_data = get_file_from_db(file_name)
        if file_data:
            # Streaming generator
            def file_iterator(file_data, chunk_size=8192):
                for i in range(0, len(file_data), chunk_size):
                    yield file_data[i:i + chunk_size]

            response = StreamingHttpResponse(file_iterator(file_data), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
        else:
            return JsonResponse({"error": f"No download link found for '{file_name}'"}, status=404)
    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {str(e)}")


@csrf_exempt
async def telegram_webhook(request):
    token = TOKEN
    application = ApplicationBuilder() \
        .token(token) \
        .read_timeout(15) \
        .write_timeout(15) \
        .connect_timeout(10) \
        .concurrent_updates(True) \
        .get_updates_read_timeout(60) \
        .get_updates_write_timeout(60) \
        .get_updates_connect_timeout(10) \
        .build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    asyncio.create_task(application.run_polling())
    
    return "Telegram webhook set up successfully."

def start_bot(request):
    run_telegram_bot.delay()
    return HttpResponse("Bot started successfully in the background.")

# @csrf_exempt
# def telegram_webhook(request):
#     bot = Bot(token=TOKEN)
#     update = Update.de_json(json.loads(request.body), bot)
#     application = Application.builder().token(TOKEN).build()
#     conv_handler = ConversationHandler(
#             entry_points=[CommandHandler('start', start)],
#     )
#     application.add_handler(conv_handler)
#     return JsonResponse({'status': 'ok'})

# @csrf_exempt
# async def telegram_webhook(request):
#     bot = Bot(token=TOKEN)
#     application = Application.builder().token(TOKEN).build()

#     async def start(update: Update, context):
#         await update.message.reply_text('Hello! Send me the name of the anime you are looking for.')

#     async def handle_message(update: Update, context):
#         anime_name = update.message.text
#         search_results = fetch_anime_search_results(anime_name)
#         if search_results:
#             results_text = '\n'.join([f"{i+1}. {title}" for i, (_, title) in enumerate(search_results)])
#             await update.message.reply_text(f"Found the following results:\n{results_text}")
#             context.user_data['search_results'] = search_results
#         else:
#             await update.message.reply_text(f"No results found for '{anime_name}'.")

#     async def select_anime(update: Update, context):
#         anime_index = int(update.message.text) - 1
#         search_results = context.user_data.get('search_results')
#         if not search_results:
#             await update.message.reply_text("Please search for anime first.")
#             return
#         anime_url = search_results[anime_index][0]
#         seasons = fetch_anime_details(anime_url)
#         if seasons:
#             seasons_text = '\n'.join([f"{i+1}. {title}" for i, (_, title) in enumerate(seasons)])
#             await update.message.reply_text(f"Select a season:\n{seasons_text}")
#             context.user_data['seasons'] = seasons
#         else:
#             await update.message.reply_text(f"No seasons found for '{anime_url}'.")

#     async def select_episode(update: Update, context):
#         season_index = int(update.message.text) - 1
#         seasons = context.user_data.get('seasons')
#         if not seasons:
#             await update.message.reply_text("Please select a season first.")
#             return
#         episode_url = seasons[season_index][0]
#         download_link = download_anime(episode_url)
#         if download_link:
#             await update.message.reply_text(f"Download link: {download_link}")
#         else:
#             await update.message.reply_text(f"No download link found for '{episode_url}'.")

#     application.add_handler(CommandHandler('start', start))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
#     application.add_handler(MessageHandler(filters.Regex(r'^\d+$'), select_anime))
#     application.add_handler(MessageHandler(filters.Regex(r'^\d+$'), select_episode))

#     if request.method == "POST":
#         update = Update.de_json(request.json(), bot)
#         await application.process_update(update)
#         return JsonResponse({'status': 'ok'})
#     else:
#         return HttpResponseBadRequest()
    
# @csrf_exempt
# def set_telegram_webhook(request):
#     set_webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
#     ngrok_url = os.environ.get("NGROK_SERVER")
#     webhook_url = f"{ngrok_url}/telegram_webhook/"

#     response = requests.post(set_webhook_url, data={"url": webhook_url})
#     return JsonResponse(response.json())
















# @csrf_exempt
# async def telegram_webhook(request):
#     logger.info("Received webhook request.")
#     try:
#         data = json.loads(request.body.decode('utf-8'))
#         logger.debug("Received data: %s", data)
        
#         message = data.get('message', {})
#         chat_id = message.get('chat', {}).get('id')
#         text = message.get('text')

#         if text:
#             log = RequestsLog(chat_id=chat_id, anime_name=text, timestamp=timezone.now())
#             log.save()

#             download_link = anime_download_link(text)
#             if download_link:
#                 try:
#                     await sync_to_async(stream_to_telegram)(os.environ.get('TELEGRAM_BOT_TOKEN'), chat_id, download_link, f"{text}.mp4")
#                     response_text = f'Here is your episode for {text}.'
#                 except Exception as e:
#                     response_text = f'Failed to stream the file: {str(e)}'
#             else:
#                 response_text = f'No episodes found for {text}'

#             bot = Bot(token=os.environ.get('TELEGRAM_BOT_TOKEN'))
#             await sync_to_async(bot.send_message)(chat_id=chat_id, text=response_text)

#             return JsonResponse({"status": "ok"})
#         else:
#             return HttpResponseBadRequest("Invalid request: 'text' field missing")
#     except json.JSONDecodeError as e:
#         logger.error("Invalid JSON data: %s", str(e))
#         return HttpResponseBadRequest("Invalid JSON data: " + str(e))
#     except Exception as e:
#         logger.error("Error processing request: %s", str(e))
#         return HttpResponseBadRequest("Error processing request: " + str(e))











    #get all the episode from the database
    # episodes = get_all_files_from_db()
    # if episodes:
    #     return JsonResponse({"episodes": episodes})
    # else:
    #     return JsonResponse({"error": "No episodes found"}, status=404)
    


    # use the file name from the request to fetch from the database using get_file_from_db function
    # file_name = request.GET.get('file_name', None)
    # if not file_name:
    #     return HttpResponseBadRequest("Parameter 'file_name' is required.")
    # try:
    #     #extract title and link from the fetch_anime_search_results and return all the title and link
    #     link = get_file_from_db(file_name)
    #     if link:
    #         # return success message with file retrieved nothin else
    #         #An error occurred: In order to allow non-dict objects to be serialized set the safe parameter to False.
    #         return JsonResponse("success",safe=False)            
    #     else:
    #         return JsonResponse({"error": f"No download link found for '{file_name}'"}, status=404)
    # except Exception as e:
    #     return HttpResponseServerError(f"An error occurred: {str(e)}")


# @require_GET
# def download_link(request):
#     ep_link = request.GET.get('ep_link', None)
#     if not ep_link:
#         return HttpResponseBadRequest("Parameter 'ep_link' is required.")
#     try:
#         link = 

# @require_GET
# def anime_download_link(request):
#     anime_name = request.GET.get('anime_name', None)
#     if not anime_name:
#         return HttpResponseBadRequest("Parameter 'anime_name' is required.")

#     try:
#         download_link = get_hianime_download_link(anime_name)
#         if download_link:
#             return JsonResponse({"anime_name": anime_name, "download_link": download_link})
#         else:
#             return JsonResponse({"error": f"No anime or episodes found for '{anime_name}'"}, status=404)
#     except Exception as e:
#         return HttpResponseServerError(f"An error occurred: {str(e)}")

# @require_GET
# def anime_download_link(request):
#     anime_name = request.GET.get('anime_name', None)
#     if not anime_name:
#         return HttpResponseBadRequest("Parameter 'anime_name' is required.")

#     try:
#         seasons = get_anime_seasons(anime_name)
#         if not seasons:
#             return JsonResponse({"error": f"No anime or episodes found for '{anime_name}'"}, status=404)

#         season_number = request.GET.get('season_number', None)
#         if not season_number:
#             return JsonResponse({"seasons": seasons})

#         season_number = int(season_number)
#         if season_number not in seasons:
#             return HttpResponseBadRequest("Invalid season number.")
#         print(seasons[season_number][0])
#         season_url = seasons[season_number][1]
#         download_link = season_url
#         season_name = seasons[season_number][0].strip()

#         episodes = list_files_in_drive_folder(download_link)
#         print(download_link)
#         if episodes:
#             return JsonResponse({"anime_name": anime_name, "season_name": season_name, "episodes": episodes})
#         else:
#             return JsonResponse({"error": "Failed to retrieve the episodes."}, status=500)
#     except Exception as e:
#         logger.exception("An error occurred while processing the request.")
#         return HttpResponseServerError(f"An error occurred: {str(e)}")



