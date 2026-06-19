from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .models import Inquiry, TripDocument, Review
from packages.models import SafariPackage
from shop.utils import get_cart
from core.decorators import permission_required

def contact(request):
    if request.method == 'POST':
        email = request.POST.get('email') or 'no-reply@successfulsafaris.com'
        Inquiry.objects.create(
            name=request.POST.get('name', 'Anonymous'),
            email=email,
            subject=request.POST.get('subject', 'General Inquiry'),
            message=request.POST.get('message', '')
        )
        messages.success(request, 'Your inquiry has been submitted successfully.')
        return redirect('contact')
    return render(request, 'contact.html', {'cart': get_cart(request)})

@login_required
def submit_review(request):
    if request.method == 'POST':
        package_id = request.POST.get('package_id')
        package = get_object_or_404(SafariPackage, id=package_id)
        
        Review.objects.create(
            user=request.user,
            rating=int(request.POST.get('rating', 5)),
            comment=request.POST.get('comment'),
            content_type=ContentType.objects.get_for_model(SafariPackage),
            object_id=package.id
        )
    return redirect('dashboard')

@login_required
@permission_required('View My Bookings')
def trip_documents(request):
    documents = TripDocument.objects.filter(booking__customer=request.user).select_related('booking')
    return render(request, 'trip-documents.html', {
        'documents': documents,
        'cart': get_cart(request)
    })
