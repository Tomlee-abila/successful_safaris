from django.urls import path
from . import views

urlpatterns = [
    path('', views.destinations, name='destinations'),
    path('<int:pk>/', views.destination_detail, name='destination_detail'),
    path('<slug:slug>/', views.destination_by_slug, name='destination_by_slug'),
]
