from django.db import models

# Create your models here.

class DownloadedFile(models.Model):
    filename = models.CharField(max_length=255)
    file_data = models.BinaryField()

    def __str__(self):
        return self.filename


class RequestsLog(models.Model):
    chat_id = models.CharField(max_length=500)
    anime_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.chat_id} requested {self.anime_name} at {self.timestamp}'