from django.db import models
from django.core.exceptions import ValidationError


class SiteSettings(models.Model):
    """Singleton holding the business contact details shown across the site.
    Editable from the admin so contact info can change without a developer."""

    business_name = models.CharField(max_length=200, default='Successful Luxury Safaris')
    footer_tagline = models.TextField(
        default='Crafting legendary African adventures since 2008. From the plains of the '
                'Serengeti to the jungles of Rwanda, we provide luxury experiences that respect the wild.'
    )
    address = models.CharField(max_length=255, default='Donholm, Nairobi')
    phone = models.CharField(max_length=50, default='+254 141 707 878')
    email = models.EmailField(default='info@successfulluxurysafaris.co.ke')
    footer_note = models.CharField(
        max_length=255,
        default='© 2026 SUCCESSFUL LUXURY SAFARIS Ltd. · ATOL Protected · IATA Accredited'
    )
    shop_enabled = models.BooleanField(
        default=True,
        help_text='Untick to temporarily close the online shop — hides the Shop link and cart, '
                   'and takes shop pages offline, without deleting any products or orders.'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('Site Settings already exists — edit the existing entry instead of creating a new one.')

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site Settings'


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
