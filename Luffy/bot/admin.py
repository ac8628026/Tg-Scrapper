from django.contrib import admin
from .models import RequestsLog,DownloadedFile

# Register your models here.
admin.site.register(RequestsLog)
# admin.site.site_header = 'Luffy Admin'
admin.site.register(DownloadedFile)