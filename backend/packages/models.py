from django.db import models
from destinations.models import SafariLocation

class SafariPackage(models.Model):
    package_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_days = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    locations = models.ManyToManyField(SafariLocation, related_name='packages')
    included_services = models.TextField(blank=True, null=True)
    excluded_services = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    featured_image = models.ImageField(upload_to='packages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.package_code})"

class PackageItinerary(models.Model):
    package = models.ForeignKey(SafariPackage, related_name='itinerary_days', on_delete=models.CASCADE)
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.ForeignKey(SafariLocation, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ('package', 'day_number')

    def __str__(self):
        return f"Day {self.day_number}: {self.title} ({self.package.package_code})"
