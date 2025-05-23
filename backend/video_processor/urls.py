from django.urls import path
from .views import UploadView, ListModelsView

urlpatterns = [
    path('upload/', UploadView.as_view(), name='upload'),
    path('models/', ListModelsView.as_view(), name='list_models'),
]