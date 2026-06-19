from django.contrib import admin
from .models import SafariPackage, PackageItinerary

class ItineraryInline(admin.TabularInline):
    model = PackageItinerary
    extra = 1

@admin.register(SafariPackage)
class SafariPackageAdmin(admin.ModelAdmin):
    list_display = ('package_code', 'title', 'duration_days', 'base_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'package_code')
    inlines = [ItineraryInline]
