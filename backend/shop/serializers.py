from rest_framework import serializers
from packages.models import SafariPackage
from .models import Product

class BundlePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafariPackage
        fields = ['id', 'title', 'description', 'base_price', 'duration_days', 'featured_image']

class BundleProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category_name', 'image']
