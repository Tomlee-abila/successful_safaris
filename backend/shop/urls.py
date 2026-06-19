from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop, name='shop'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('api/bundle-options/', views.BundleOptionsAPIView.as_view(), name='bundle_options_api'),
    path('bundle-builder/', views.bundle_builder, name='bundle_builder'),
    path('cart/', views.shopping_cart, name='shopping_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
]
