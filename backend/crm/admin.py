from django.contrib import admin
from .models import Inquiry, Review, TripDocument

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'content_type', 'object_id', 'created_at')
    list_filter = ('rating', 'content_type')

@admin.register(TripDocument)
class TripDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'booking', 'document_type')
    list_filter = ('document_type',)
