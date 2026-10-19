from destinations.models import Destination, SafariLocation, Accommodation
from packages.models import SafariPackage
from blog.models import BlogCategory, BlogPost
from shop.models import ProductCategory, Product
from crm.models import TripDocument

from . import forms as f

# Each entry describes one manageable content type: the model, the form to
# use for add/edit, what columns the list table shows, and which fields
# the search box matches against.
SECTIONS = {
    'packages': {
        'label': 'Safari Packages', 'singular': 'Safari Package', 'icon': '🦁', 'model': SafariPackage,
        'form_class': f.SafariPackageForm,
        'list_fields': [('title', 'Title'), ('package_code', 'Code'),
                          ('duration_days', 'Days'), ('base_price', 'Price'), ('is_active', 'Active')],
        'search_fields': ['title', 'package_code'],
        'order_by': '-created_at', 'group': 'Content',
    },
    'destinations': {
        'label': 'Destinations', 'singular': 'Destination', 'icon': '🌍', 'model': Destination,
        'form_class': f.DestinationForm,
        'list_fields': [('name', 'Name'), ('best_travel_season', 'Best Season')],
        'search_fields': ['name'], 'order_by': 'name', 'group': 'Content',
    },
    'locations': {
        'label': 'Safari Locations', 'singular': 'Safari Location', 'icon': '📍', 'model': SafariLocation,
        'form_class': f.SafariLocationForm,
        'list_fields': [('name', 'Name'), ('destination', 'Destination')],
        'search_fields': ['name'], 'order_by': 'name', 'group': 'Content',
    },
    'accommodations': {
        'label': 'Lodges & Camps', 'singular': 'Lodge / Camp', 'icon': '🏕️', 'model': Accommodation,
        'form_class': f.AccommodationForm,
        'list_fields': [('name', 'Name'), ('location', 'Location'), ('type', 'Type'), ('nightly_rate', 'Nightly Rate')],
        'search_fields': ['name'], 'order_by': 'name', 'group': 'Content',
    },
    'blog-categories': {
        'label': 'Blog Categories', 'singular': 'Blog Category', 'icon': '🏷️', 'model': BlogCategory,
        'form_class': f.BlogCategoryForm,
        'list_fields': [('name', 'Name')],
        'search_fields': ['name'], 'order_by': 'name', 'group': 'Content',
    },
    'blog-posts': {
        'label': 'Blog Posts', 'singular': 'Blog Post', 'icon': '📝', 'model': BlogPost,
        'form_class': f.BlogPostForm,
        'list_fields': [('title', 'Title'), ('category', 'Category'), ('is_published', 'Published'), ('created_at', 'Created')],
        'search_fields': ['title'], 'order_by': '-created_at', 'group': 'Content',
        'extra_save': 'author',
    },
    'product-categories': {
        'label': 'Shop Categories', 'singular': 'Shop Category', 'icon': '🏷️', 'model': ProductCategory,
        'form_class': f.ProductCategoryForm,
        'list_fields': [('name', 'Name')],
        'search_fields': ['name'], 'order_by': 'name', 'group': 'Shop',
    },
    'products': {
        'label': 'Shop Products', 'singular': 'Shop Product', 'icon': '🛍️', 'model': Product,
        'form_class': f.ProductForm,
        'list_fields': [('name', 'Name'), ('sku', 'SKU'), ('category', 'Category'),
                          ('price', 'Price'), ('stock_quantity', 'Stock'), ('is_active', 'Active')],
        'search_fields': ['name', 'sku'], 'order_by': 'name', 'group': 'Shop',
    },
    'trip-documents': {
        'label': 'Trip Documents', 'singular': 'Trip Document', 'icon': '📄', 'model': TripDocument,
        'form_class': f.TripDocumentForm,
        'list_fields': [('title', 'Title'), ('booking', 'Booking'), ('document_type', 'Type')],
        'search_fields': ['title'], 'order_by': '-created_at', 'group': 'Bookings',
    },
}
