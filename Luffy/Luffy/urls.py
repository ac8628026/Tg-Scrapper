"""
URL configuration for Luffy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bot.views import (
    telegram_webhook,
    anime_download_link,
    anime_season_details,
    episode_link,
    episode,
    start_bot
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', telegram_webhook),
    path('anime_download/', anime_download_link),
    path('get_seasons/',anime_season_details),
    path('episode_link/',episode_link),
    path('episode/',episode),
    path('start_bot/',start_bot)
    # path('set_webhook/',set_telegram_webhook,name='set_webhook')
]
