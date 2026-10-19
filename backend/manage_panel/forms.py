from django import forms
from django.utils.text import slugify

from destinations.models import Destination, SafariLocation, Accommodation
from packages.models import SafariPackage, PackageItinerary
from blog.models import BlogCategory, BlogPost
from shop.models import ProductCategory, Product
from crm.models import TripDocument
from core.models import SiteSettings


class StyledForm(forms.ModelForm):
    """Applies the site's form styling to every field automatically,
    so each specific form below doesn't need to repeat widget CSS classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = (existing + ' form-checkbox').strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(widget, forms.Textarea):
                widget.attrs['class'] = (existing + ' form-textarea').strip()
                widget.attrs.setdefault('rows', 4)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs['class'] = (existing + ' form-file').strip()
            else:
                widget.attrs['class'] = (existing + ' form-input').strip()


class SiteSettingsForm(StyledForm):
    class Meta:
        model = SiteSettings
        fields = ['business_name', 'footer_tagline', 'address', 'phone', 'email', 'footer_note', 'shop_enabled']
        labels = {'shop_enabled': 'Shop is open'}


class DestinationForm(StyledForm):
    class Meta:
        model = Destination
        fields = ['name', 'description', 'hero_image', 'best_travel_season',
                   'visa_information', 'health_requirements', 'featured_wildlife']


class SafariLocationForm(StyledForm):
    class Meta:
        model = SafariLocation
        fields = ['destination', 'name', 'description', 'activities', 'wildlife',
                   'featured_image', 'latitude', 'longitude']
        labels = {'latitude': 'Map Latitude (optional)', 'longitude': 'Map Longitude (optional)'}


class AccommodationForm(StyledForm):
    class Meta:
        model = Accommodation
        fields = ['location', 'name', 'type', 'description', 'capacity', 'nightly_rate',
                   'amenities', 'featured_image']


class SafariPackageForm(StyledForm):
    class Meta:
        model = SafariPackage
        fields = ['package_code', 'title', 'description', 'duration_days', 'base_price',
                   'locations', 'included_services', 'excluded_services',
                   'is_active', 'is_featured', 'featured_image']


class PackageItineraryForm(StyledForm):
    class Meta:
        model = PackageItinerary
        fields = ['day_number', 'title', 'description', 'location']


PackageItineraryFormSet = forms.inlineformset_factory(
    SafariPackage, PackageItinerary, form=PackageItineraryForm,
    extra=1, can_delete=True,
)


class BlogCategoryForm(StyledForm):
    class Meta:
        model = BlogCategory
        fields = ['name']

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = slugify(obj.name)
        if commit:
            obj.save()
        return obj


class BlogPostForm(StyledForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'category', 'content', 'featured_image', 'is_published']

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = slugify(obj.title)
        if commit:
            obj.save()
        return obj


class ProductCategoryForm(StyledForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = slugify(obj.name)
        if commit:
            obj.save()
        return obj


class ProductForm(StyledForm):
    class Meta:
        model = Product
        fields = ['category', 'sku', 'name', 'description', 'price', 'stock_quantity',
                   'low_stock_threshold', 'image', 'is_active']


class TripDocumentForm(StyledForm):
    class Meta:
        model = TripDocument
        fields = ['booking', 'title', 'document_type', 'file_url']
        labels = {'file_url': 'Document Link (URL)'}
