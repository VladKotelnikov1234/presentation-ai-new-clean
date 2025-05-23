from django.urls import path
from .views import UploadView, ListModelsView

urlpatterns = [
    path('api/upload/', UploadView.as_view(), name='upload'),
    path('api/models/', ListModelsView.as_view(), name='list_models'),
]