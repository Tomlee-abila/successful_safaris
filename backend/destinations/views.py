from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Min
from .models import Destination
from shop.utils import get_cart
from core.decorators import permission_required

@permission_required('Browse Destinations & Packages')
def destinations(request):
    all_destinations = Destination.objects.annotate(
        package_count=Count('locations__packages', distinct=True),
        min_price=Min('locations__packages__base_price')
    )
    return render(request, 'destinations.html', {'destinations': all_destinations, 'cart': get_cart(request)})

@permission_required('Browse Destinations & Packages')
def destination_detail(request, pk):
    destination = get_object_or_404(Destination.objects.annotate(
        package_count=Count('locations__packages', distinct=True),
        min_price=Min('locations__packages__base_price')
    ), pk=pk)
    
    locations = destination.locations.all().prefetch_related('accommodations')
    
    wildlife_list = []
    if destination.featured_wildlife:
        wildlife_list = [w.strip() for w in destination.featured_wildlife.split(',')]
    
    return render(request, 'destination-detail.html', {
        'destination': destination,
        'locations': locations,
        'wildlife_list': wildlife_list,
        'cart': get_cart(request)
    })

@permission_required('Browse Destinations & Packages')
def destination_by_slug(request, slug):
    destination = get_object_or_404(Destination.objects.annotate(
        package_count=Count('locations__packages', distinct=True),
        min_price=Min('locations__packages__base_price')
    ), name__iexact=slug)
    
    if slug.lower() == 'kenya':
        return render(request, 'destination-kenya.html', {'destination': destination, 'cart': get_cart(request)})
    
    locations = destination.locations.all().prefetch_related('accommodations')
    
    wildlife_list = []
    if destination.featured_wildlife:
        wildlife_list = [w.strip() for w in destination.featured_wildlife.split(',')]
        
    return render(request, 'destination-detail.html', {
        'destination': destination,
        'locations': locations,
        'wildlife_list': wildlife_list,
        'cart': get_cart(request)
    })

