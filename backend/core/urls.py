from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('destinations/', views.destinations, name='destinations'),
    path('destinations/kenya/', lambda r: render(r, 'destination-kenya.html'), name='destination_kenya'),
    path('destinations/tanzania/', views.destination_detail, name='destination_tanzania'),
    path('packages/', views.packages, name='packages'),
    path('packages/detail/', views.package_detail, name='package_detail'),
    path('shop/', views.shop, name='shop'),
    path('shop/product/', views.product_detail, name='product_detail'),
    path('shop/bundle-builder/', views.bundle_builder, name='bundle_builder'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('auth/', views.auth, name='auth'),
    path('booking/', views.booking, name='booking'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('style-guide/', views.style_guide, name='style_guide'),
    path('wireframes/', views.wireframes, name='wireframes'),
    path('trip-documents/', views.trip_documents, name='trip_documents'),
    path('shop/cart/', views.shopping_cart, name='shopping_cart'),
]
