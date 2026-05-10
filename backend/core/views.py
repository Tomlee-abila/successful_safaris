from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def destinations(request):
    return render(request, 'destinations.html')

def destination_detail(request):
    return render(request, 'destination-detail.html')

def packages(request):
    return render(request, 'packages.html')

def package_detail(request):
    return render(request, 'package-detail.html')

def shop(request):
    return render(request, 'shop.html')

def product_detail(request):
    return render(request, 'product-detail.html')

def bundle_builder(request):
    return render(request, 'bundle-builder.html')

def blog(request):
    return render(request, 'blog.html')

def contact(request):
    return render(request, 'contact.html')

def auth(request):
    return render(request, 'auth.html')

def booking(request):
    return render(request, 'booking.html')

def checkout(request):
    return render(request, 'checkout.html')

def order_confirmation(request):
    return render(request, 'order-confirmation.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def admin_dashboard(request):
    return render(request, 'admin-dashboard.html')

def sitemap(request):
    return render(request, 'sitemap.html')

def style_guide(request):
    return render(request, 'style-guide.html')

def wireframes(request):
    return render(request, 'wireframes.html')

def trip_documents(request):
    return render(request, 'trip-documents.html')

def shopping_cart(request):
    return render(request, 'shopping-cart.html')
