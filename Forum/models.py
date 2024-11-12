from django.db import models
from django.conf import settings


# Функция для динамического формирования пути загрузки файла
def user_directory_path(instance, filename):
    return f'images/{instance.user.username}/{filename}'


class ImageModel(models.Model):
    objects = None
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=user_directory_path)
    date = models.DateTimeField()
