from django.urls import path
from . import views

urlpatterns = [
    path('contact/', views.contact, name='contact'),
    path('review/submit/', views.submit_review, name='submit_review'),
    path('trip-documents/', views.trip_documents, name='trip_documents'),
]
