from django.urls import path
from Forum.views import *

urlpatterns = [
    path('', authorization, name='authorization'),
    path('index/', index, name='index'),
    path('logout/', user_logout, name='logout'),
    path('upload/', upload_file, name='upload_file'),
    path('delete/<int:image_id>/', delete_image, name='delete_image'),
]