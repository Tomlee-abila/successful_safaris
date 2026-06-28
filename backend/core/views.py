from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Min
from destinations.models import Destination
from packages.models import SafariPackage
from inventory.models import Page, Module
from crm.models import Review
from shop.utils import get_cart
from .models import NewsletterSubscriber

def home(request):
    top_destinations = Destination.objects.annotate(
        package_count=Count('locations__packages', distinct=True),
        min_price=Min('locations__packages__base_price')
    )[:5]
    featured_packages = SafariPackage.objects.filter(is_active=True).prefetch_related('locations')[:3]
    testimonials = Review.objects.filter(rating__gte=4).select_related('user').order_by('-id')[:3]
    context = {
        'top_destinations': top_destinations,
        'featured_packages': featured_packages,
        'testimonials': testimonials,
        'cart': get_cart(request),
    }
    return render(request, 'home.html', context)

def about(request):
    return render(request, 'about.html', {'cart': get_cart(request)})

def sitemap(request):
    pages = Page.objects.all().order_by('code')
    modules = Module.objects.all()
    pages_by_access = {
        'PUBLIC': pages.filter(access_level='PUBLIC'),
        'USER': pages.filter(access_level='USER'),
        'SUBADMIN': pages.filter(access_level='SUBADMIN'),
        'SUPERADMIN': pages.filter(access_level='SUPERADMIN'),
    }
    return render(request, 'sitemap.html', {'pages_by_access': pages_by_access, 'modules': modules, 'cart': get_cart(request)})

def wireframes(request): return render(request, 'wireframes.html', {'cart': get_cart(request)})
def style_guide(request): return render(request, 'style-guide.html', {'cart': get_cart(request)})

@require_POST
def newsletter_subscribe(request):
    email = request.POST.get('email', '').strip()
    if not email or '@' not in email:
        return JsonResponse({'status': 'error', 'message': 'Please enter a valid email address.'})
    _, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if created:
        return JsonResponse({'status': 'success', 'message': 'You\'re on the list! Thank you for joining.'})
    return JsonResponse({'status': 'already', 'message': 'You\'re already subscribed — we\'ll be in touch!'})
