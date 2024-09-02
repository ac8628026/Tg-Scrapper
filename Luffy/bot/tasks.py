from celery import shared_task

@shared_task
def run_telegram_bot():
    from run_polling import run_polling
    run_polling()