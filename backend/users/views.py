from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Sum
from django.views.decorators.http import require_POST
import pyotp
import qrcode
import qrcode.image.svg
import base64
import io

from .models import UserProfile, Wishlist
from inventory.models import Permission
from bookings.models import Booking
from shop.models import Order
from crm.models import TripDocument, Review
from shop.utils import get_cart
from core.decorators import permission_required


# ── Auth ───────────────────────────────────────────────────────────────

def auth(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email_or_username, password=password)
        if user is None:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            # MFA check: if enabled, hold the user in session and redirect
            profile = getattr(user, 'profile', None)
            if profile and profile.mfa_enabled:
                request.session['mfa_pending_user_id'] = user.pk
                return redirect('mfa_verify')
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth.html', {'error': 'Invalid credentials', 'cart': get_cart(request)})
    return render(request, 'auth.html', {'cart': get_cart(request)})


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        errors = {}
        if User.objects.filter(username=username).exists():
            errors['username'] = ['Taken.']
        if User.objects.filter(email=email).exists():
            errors['email'] = ['Exists.']
        if not errors:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            customer_group, _ = Group.objects.get_or_create(name='Customer')
            user.groups.add(customer_group)
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
        return render(request, 'register.html', {'errors': errors, 'cart': get_cart(request)})
    return render(request, 'register.html', {'cart': get_cart(request)})


# ── Dashboard ──────────────────────────────────────────────────────────

@permission_required('View My Bookings')
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_groups = request.user.groups.values_list('name', flat=True)
    primary_group = user_groups[0] if user_groups else 'Customer'
    permissions = Permission.objects.filter(role=primary_group, can_view=True).select_related('module')

    upcoming_bookings = Booking.objects.filter(
        customer=request.user,
        status__in=['PENDING', 'CONFIRMED'],
        start_date__gte=timezone.now().date()
    ).order_by('start_date').prefetch_related('package__locations')

    past_bookings = Booking.objects.filter(
        customer=request.user,
        status='COMPLETED'
    ).order_by('-start_date').prefetch_related('package__locations')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    documents = TripDocument.objects.filter(booking__customer=request.user).select_related('booking')
    reviews = Review.objects.filter(user=request.user)

    total_spent = Booking.objects.filter(
        customer=request.user,
        status='COMPLETED'
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('package').order_by('-created_at')

    context = {
        'profile': profile,
        'role': primary_group,
        'permissions': permissions,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'orders': orders,
        'documents': documents,
        'reviews': reviews,
        'upcoming_count': upcoming_bookings.count(),
        'past_count': past_bookings.count(),
        'order_count': orders.count(),
        'doc_count': documents.count(),
        'total_spent': total_spent,
        'reward_value': profile.loyalty_points // 20,
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_items.count(),
        'cart': get_cart(request),
    }
    return render(request, 'dashboard.html', context)


def profile_update(request):
    if request.method == 'POST':
        profile, user = request.user.profile, request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        profile.phone = request.POST.get('phone')
        profile.nationality = request.POST.get('nationality')
        profile.passport_number = request.POST.get('passport_number')
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
    return redirect('dashboard')


# ── MFA ────────────────────────────────────────────────────────────────

def _generate_qr_data_uri(secret, username):
    """Return base64-encoded PNG data URI of the TOTP QR code."""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name='Successful Safaris')
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'data:image/png;base64,{b64}'


@login_required
def mfa_setup(request):
    """Show the QR code for TOTP enrollment."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    # Generate a fresh secret each time the setup page is loaded (not yet saved)
    secret = pyotp.random_base32()
    request.session['mfa_temp_secret'] = secret
    qr_uri = _generate_qr_data_uri(secret, request.user.username)
    return render(request, 'mfa_setup.html', {
        'qr_uri': qr_uri,
        'secret': secret,
        'cart': get_cart(request),
    })


@login_required
def mfa_confirm(request):
    """Validate the first TOTP token and save the secret."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        secret = request.session.get('mfa_temp_secret')
        if not secret:
            return redirect('mfa_setup')
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.mfa_secret = secret
            profile.mfa_enabled = True
            profile.save()
            del request.session['mfa_temp_secret']
            return redirect('dashboard')
        else:
            secret = request.session.get('mfa_temp_secret')
            qr_uri = _generate_qr_data_uri(secret, request.user.username)
            return render(request, 'mfa_setup.html', {
                'qr_uri': qr_uri,
                'secret': secret,
                'error': 'Invalid code — please try again.',
                'cart': get_cart(request),
            })
    return redirect('mfa_setup')


@login_required
@require_POST
def mfa_disable(request):
    """Disable MFA for the logged-in user."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.mfa_enabled = False
    profile.mfa_secret = ''
    profile.save()
    return redirect('dashboard')


def mfa_verify(request):
    """Second-factor TOTP verification step during login."""
    pending_id = request.session.get('mfa_pending_user_id')
    if not pending_id:
        return redirect('auth')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        try:
            user = User.objects.get(pk=pending_id)
            profile = user.profile
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return redirect('auth')

        totp = pyotp.TOTP(profile.mfa_secret)
        if totp.verify(code, valid_window=1):
            del request.session['mfa_pending_user_id']
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
        else:
            return render(request, 'mfa_verify.html', {
                'error': 'Invalid code. Please try again.',
                'cart': get_cart(request),
            })

    return render(request, 'mfa_verify.html', {'cart': get_cart(request)})


# ── WISHLIST ────────────────────────────────────────────────────────────

@login_required
@require_POST
def wishlist_toggle(request):
    from packages.models import SafariPackage
    from django.http import JsonResponse
    pkg_id = request.POST.get('package_id')
    package = SafariPackage.objects.get(pk=pkg_id)
    item, created = Wishlist.objects.get_or_create(user=request.user, package=package)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed', 'count': request.user.wishlist_items.count()})
    return JsonResponse({'status': 'added', 'count': request.user.wishlist_items.count()})


# Update dashboard to include wishlist data
# (wishlist_items are fetched in the existing dashboard view via context addition below)
