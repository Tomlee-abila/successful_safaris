from django.contrib import admin
from django.shortcuts import redirect
from .models import SiteSettings, NewsletterSubscriber


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'phone', 'email', 'address')

    def has_add_permission(self, request):
        # Singleton: only allow adding if no row exists yet.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip the list page and go straight to editing the one settings row.
        obj = SiteSettings.get_solo()
        return redirect('admin:core_sitesettings_change', obj.pk)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
