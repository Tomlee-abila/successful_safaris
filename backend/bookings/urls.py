from django.urls import path
from . import views

urlpatterns = [
    path('booking/', views.booking, name='booking'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirmation/', views.order_confirmation, name='order_confirmation'),
]
