from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nationality', 'loyalty_tier', 'loyalty_points')
    list_filter = ('loyalty_tier', 'nationality')
    search_fields = ('user__username', 'passport_number')
