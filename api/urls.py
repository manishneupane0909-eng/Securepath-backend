from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('status/', views.status_check, name='status'),
    path('upload/', views.upload_csv_view, name='upload-csv'),
    path('train-model/', views.train_model, name='train-model'),
]
