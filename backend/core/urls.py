from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('style-guide/', views.style_guide, name='style_guide'),
    path('wireframes/', views.wireframes, name='wireframes'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
