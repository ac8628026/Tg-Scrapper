# """
# ASGI config for Luffy project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
# """

# import os
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Luffy.settings')
# import django
# django.setup()
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.sessions import SessionMiddlewareStack
# from django.urls import path
# from .consumers import TelegramConsumer
# print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

# # application = get_asgi_application()
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": SessionMiddlewareStack(
#         URLRouter([
#             # Define your websocket routes here
#             path('ws/telegram/', TelegramConsumer.as_asgi()),
#         ])
#     ),
# })
