# points/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('download-image/', views.download_image, name='download_image'),
]
