from django.contrib import admin
from .models import Booking, Traveler, Payment

class TravelerInline(admin.TabularInline):
    model = Traveler
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'customer', 'package', 'status', 'total_amount')
    list_filter = ('status', 'start_date')
    search_fields = ('booking_number', 'customer__username')
    inlines = [TravelerInline, PaymentInline]
