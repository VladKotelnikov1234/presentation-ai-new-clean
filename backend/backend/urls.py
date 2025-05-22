from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('video_processor.urls')), 
    path('', lambda request: HttpResponse("Сервер работает!")),
]