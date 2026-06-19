from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from bookings.models import Booking

class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Inquiry from {self.name} - {self.subject}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField() # 1 to 5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Generic relation to review Packages, Products, or Destinations
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Review by {self.user.username} - {self.rating} stars"

class TripDocument(models.Model):
    DOCUMENT_TYPES = [
        ('ITINERARY', 'Itinerary'),
        ('INVOICE', 'Invoice'),
        ('PERMIT', 'Park Permit'),
        ('INSURANCE', 'Insurance Document'),
        ('GUIDE', 'Travel Guide'),
    ]
    booking = models.ForeignKey(Booking, related_name='documents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} for {self.booking.booking_number}"
