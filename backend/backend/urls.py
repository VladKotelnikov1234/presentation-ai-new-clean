from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('video_processor.urls')),
    path('', TemplateView.as_view(template_name='index.html')),  # Главная страница фронтенда
    re_path(r'^(?!api/).*', TemplateView.as_view(template_name='index.html')),  # Все маршруты, кроме API, отдают index.html
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)