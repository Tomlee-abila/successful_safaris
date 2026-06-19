from django.urls import path
from . import views

urlpatterns = [
    path('', views.packages, name='packages'),
    path('<int:pk>/', views.package_detail, name='package_detail'),
]
