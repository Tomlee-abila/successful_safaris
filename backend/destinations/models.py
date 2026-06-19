from django.db import models

class Destination(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    hero_image = models.ImageField(upload_to='destinations/heroes/', blank=True, null=True)
    best_travel_season = models.CharField(max_length=200, blank=True, null=True)
    visa_information = models.TextField(blank=True, null=True)
    health_requirements = models.TextField(blank=True, null=True)
    featured_wildlife = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class SafariLocation(models.Model):
    destination = models.ForeignKey(Destination, related_name='locations', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    activities = models.TextField(blank=True, null=True)
    wildlife = models.TextField(blank=True, null=True)
    featured_image = models.ImageField(upload_to='locations/', blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.destination.name})"

class Accommodation(models.Model):
    ACCOMMODATION_TYPES = [
        ('LODGE', 'Luxury Lodge'),
        ('CAMP', 'Tented Camp'),
        ('VILLA', 'Private Villa'),
        ('HOTEL', 'Hotel'),
    ]
    location = models.ForeignKey(SafariLocation, related_name='accommodations', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=ACCOMMODATION_TYPES, default='LODGE')
    description = models.TextField()
    capacity = models.IntegerField(default=20)
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField(blank=True, null=True)
    featured_image = models.ImageField(upload_to='accommodations/', blank=True, null=True)

    def __str__(self):
        return self.name
