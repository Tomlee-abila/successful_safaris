from django.contrib import admin
from .models import Destination, SafariLocation, Accommodation

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'best_travel_season')
    search_fields = ('name',)

@admin.register(SafariLocation)
class SafariLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'destination')
    list_filter = ('destination',)
    search_fields = ('name',)

@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'type', 'nightly_rate')
    list_filter = ('type', 'location__destination')
    search_fields = ('name',)
