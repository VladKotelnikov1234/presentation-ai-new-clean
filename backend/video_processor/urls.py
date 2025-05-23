from django.urls import path
from .views import UploadView

urlpatterns = [
    path('api/upload/', UploadView.as_view(), name='upload'),
]