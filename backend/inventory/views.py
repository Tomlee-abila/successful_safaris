from django.shortcuts import render
from django.db import models
from django.db.models import Sum
from rest_framework import viewsets
from .models import Page, Module, Permission
from .serializers import PageSerializer, ModuleSerializer, PermissionSerializer
from shop.models import Product, Order
from bookings.models import Booking
from shop.utils import get_cart
from core.decorators import permission_required

class PageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all().order_by('code')
    serializer_class = PageSerializer

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ['role', 'module__name']

@permission_required('View Analytics (Limited)')
def admin_dashboard(request):
    # ── BUSINESS KPIs ──
    # 1. Revenue
    total_revenue = Order.objects.filter(status='PAID').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    booking_revenue = Booking.objects.filter(status__in=['CONFIRMED', 'COMPLETED']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    grand_total_revenue = total_revenue + booking_revenue
    
    # 2. Bookings & Orders
    active_bookings_count = Booking.objects.filter(status__in=['PENDING', 'CONFIRMED']).count()
    new_orders_count = Order.objects.filter(status='PENDING').count()
    
    # 3. Inventory Alerts
    low_stock_products = Product.objects.filter(stock_quantity__lte=models.F('low_stock_threshold'), is_active=True)
    alert_count = low_stock_products.count()
    
    # 4. Recent Activity
    recent_bookings = Booking.objects.all().order_by('-created_at')[:5]
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    context = {
        'revenue': grand_total_revenue,
        'active_bookings': active_bookings_count,
        'new_orders': new_orders_count,
        'alerts': alert_count,
        'low_stock_products': low_stock_products,
        'recent_bookings': recent_bookings,
        'recent_orders': recent_orders,
        'cart': get_cart(request),
    }
    return render(request, 'admin-dashboard.html', context)
