from django.shortcuts import render, get_object_or_404
from .models import SafariPackage
from shop.utils import get_cart
from core.decorators import permission_required

@permission_required('Browse Destinations & Packages')
def packages(request):
    all_packages = SafariPackage.objects.filter(is_active=True).prefetch_related('locations')
    return render(request, 'packages.html', {
        'packages': all_packages,
        'cart': get_cart(request)
    })

@permission_required('Browse Destinations & Packages')
def package_detail(request, pk):
    package = get_object_or_404(SafariPackage.objects.prefetch_related('locations__destination', 'itinerary_days'), pk=pk)
    return render(request, 'package-detail.html', {
        'package': package,
        'cart': get_cart(request)
    })
