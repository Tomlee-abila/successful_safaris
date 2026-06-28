from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import ProductCategory, Product, CartItem
from .utils import get_cart
from core.decorators import permission_required

from rest_framework.views import APIView
from rest_framework.response import Response
from packages.models import SafariPackage
from .serializers import BundlePackageSerializer, BundleProductSerializer

class BundleOptionsAPIView(APIView):
    def get(self, request):
        packages = SafariPackage.objects.filter(is_active=True)[:4]
        gear = Product.objects.filter(category__name__icontains='Gear', is_active=True)[:6]
        addons = Product.objects.filter(category__name__icontains='Add-on', is_active=True)[:6]
        
        # If no specific categories found, just take some products
        if not gear.exists():
            gear = Product.objects.filter(is_active=True)[:4]
        
        return Response({
            'packages': BundlePackageSerializer(packages, many=True).data,
            'gear': BundleProductSerializer(gear, many=True).data,
            'addons': BundleProductSerializer(addons, many=True).data,
        })

@permission_required('Browse Shop / Products')
def shop(request):
    categories = ProductCategory.objects.all()
    products = Product.objects.filter(is_active=True)
    context = {
        'categories': categories,
        'products': products,
        'cart': get_cart(request),
    }
    return render(request, 'shop.html', context)

@permission_required('Browse Shop / Products')
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, 'product-detail.html', {
        'product': product,
        'related_products': related_products,
        'cart': get_cart(request)
    })

def bundle_builder(request):
    return render(request, 'bundle-builder.html', {'cart': get_cart(request)})

# ── CART ACTIONS ──

def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'status': 'success', 'cart_count': cart.items.count()})
    return JsonResponse({'status': 'error'}, status=400)

def shopping_cart(request):
    cart = get_cart(request)
    return render(request, 'shopping-cart.html', {'cart': cart})

def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
        if action == 'increase': cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1: cart_item.quantity -= 1
        cart_item.save()
        return redirect('shopping_cart')
    return redirect('shopping_cart')

def remove_from_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        cart_item = get_object_or_404(CartItem, id=item_id, cart=get_cart(request))
        cart_item.delete()
    return redirect('shopping_cart')

def cart_data(request):
    cart = get_cart(request)
    items = []
    for item in cart.items.select_related('product'):
        items.append({
            'id': item.id,
            'name': item.product.name,
            'price': float(item.product.price),
            'quantity': item.quantity,
            'subtotal': float(item.product.price * item.quantity),
            'image': item.product.image.url if item.product.image else None,
        })
    total = sum(i['subtotal'] for i in items)
    return JsonResponse({'items': items, 'count': len(items), 'total': total})
