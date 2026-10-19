from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_POST

from bookings.models import Booking
from shop.models import Order
from crm.models import Inquiry, Review
from core.models import NewsletterSubscriber, SiteSettings

from .registry import SECTIONS


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('auth')}?{urlencode({'next': request.get_full_path()})}")
        if not request.user.is_staff:
            messages.error(request, "You don't have access to the management panel.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapped


def superuser_required(view_func):
    """Stricter than staff_required — for actions that touch real hosting
    infrastructure (creating/deleting actual mailboxes), not just website
    content."""
    @wraps(view_func)
    @staff_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Only a super admin can manage staff email accounts.")
            return redirect('manage:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped


def _section_or_404(slug):
    section = SECTIONS.get(slug)
    if not section:
        raise Http404("Unknown section")
    return section


def _nav_groups():
    groups = {}
    for slug, section in SECTIONS.items():
        groups.setdefault(section['group'], []).append((slug, section))
    return groups


def _base_context(request, active_slug=None):
    return {
        'nav_groups': _nav_groups(),
        'active_slug': active_slug,
        'cart': None,
    }


@staff_required
def dashboard(request):
    ctx = _base_context(request)
    ctx.update({
        'bookings_count': Booking.objects.count(),
        'orders_count': Order.objects.count(),
        'inquiries_open': Inquiry.objects.filter(is_resolved=False).count(),
        'subscribers_count': NewsletterSubscriber.objects.count(),
        'recent_inquiries': Inquiry.objects.order_by('-created_at')[:5],
        'recent_bookings': Booking.objects.order_by('-created_at')[:5],
    })
    return render(request, 'manage/dashboard.html', ctx)


@staff_required
def site_settings_edit(request):
    obj = SiteSettings.get_solo()
    from .forms import SiteSettingsForm
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings updated.")
            return redirect('manage:site_settings')
    else:
        form = SiteSettingsForm(instance=obj)
    ctx = _base_context(request, active_slug='site-settings')
    ctx.update({'form': form, 'title': 'Site Settings'})
    return render(request, 'manage/site_settings_form.html', ctx)


@staff_required
def list_view(request, slug):
    section = _section_or_404(slug)
    qs = section['model'].objects.all()
    if section.get('order_by'):
        qs = qs.order_by(section['order_by'])
    query = request.GET.get('q', '').strip()
    if query and section.get('search_fields'):
        condition = Q()
        for field in section['search_fields']:
            condition |= Q(**{f'{field}__icontains': query})
        qs = qs.filter(condition)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    ctx = _base_context(request, active_slug=slug)
    ctx.update({
        'section': section, 'slug': slug, 'page_obj': page_obj, 'query': query,
        'title': section['label'],
    })
    return render(request, 'manage/list.html', ctx)


@staff_required
def add_view(request, slug):
    section = _section_or_404(slug)
    if slug == 'packages':
        return _package_form(request, package=None)

    FormClass = section['form_class']
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if section.get('extra_save') == 'author':
                obj.author = request.user
            obj.save()
            form.save_m2m()
            messages.success(request, f"{section['singular']} added.")
            return redirect('manage:list', slug=slug)
    else:
        form = FormClass()
    ctx = _base_context(request, active_slug=slug)
    ctx.update({'section': section, 'slug': slug, 'form': form, 'title': f"Add {section['singular']}"})
    return render(request, 'manage/form.html', ctx)


@staff_required
def edit_view(request, slug, pk):
    section = _section_or_404(slug)
    instance = get_object_or_404(section['model'], pk=pk)
    if slug == 'packages':
        return _package_form(request, package=instance)

    FormClass = section['form_class']
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{section['singular']} updated.")
            return redirect('manage:list', slug=slug)
    else:
        form = FormClass(instance=instance)
    ctx = _base_context(request, active_slug=slug)
    ctx.update({'section': section, 'slug': slug, 'form': form, 'instance': instance,
                 'title': f"Edit {instance}"})
    return render(request, 'manage/form.html', ctx)


@staff_required
def delete_view(request, slug, pk):
    section = _section_or_404(slug)
    instance = get_object_or_404(section['model'], pk=pk)
    if request.method == 'POST':
        label = str(instance)
        instance.delete()
        messages.success(request, f'"{label}" was deleted.')
        return redirect('manage:list', slug=slug)
    ctx = _base_context(request, active_slug=slug)
    ctx.update({'section': section, 'slug': slug, 'instance': instance})
    return render(request, 'manage/delete_confirm.html', ctx)


def _package_form(request, package):
    from .forms import SafariPackageForm, PackageItineraryFormSet
    from packages.models import SafariPackage
    section = SECTIONS['packages']
    if request.method == 'POST':
        form = SafariPackageForm(request.POST, request.FILES, instance=package)
        # Validate the itinerary against the existing (or a blank, unsaved) package
        # instance first, so a bad itinerary never leaves an orphaned package row —
        # both must be valid before either is saved.
        formset = PackageItineraryFormSet(request.POST, instance=package or SafariPackage())
        if form.is_valid() and formset.is_valid():
            obj = form.save()
            formset.instance = obj
            formset.save()
            messages.success(request, "Package saved.")
            return redirect('manage:list', slug='packages')
    else:
        form = SafariPackageForm(instance=package)
        formset = PackageItineraryFormSet(instance=package)
    ctx = _base_context(request, active_slug='packages')
    ctx.update({
        'section': section, 'slug': 'packages', 'form': form, 'formset': formset,
        'instance': package, 'title': f"Edit {package}" if package else "Add Safari Package",
    })
    return render(request, 'manage/package_form.html', ctx)


@staff_required
def booking_list(request):
    qs = Booking.objects.select_related('customer', 'package').order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(Q(booking_number__icontains=query) | Q(customer__username__icontains=query))
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='bookings')
    ctx.update({'page_obj': page_obj, 'query': query, 'title': 'Bookings'})
    return render(request, 'manage/booking_list.html', ctx)


@staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking.objects.select_related('customer', 'package'), pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Booking.STATUS_CHOICES):
            booking.status = status
            booking.save()
            messages.success(request, "Booking status updated.")
        return redirect('manage:booking_detail', pk=pk)
    ctx = _base_context(request, active_slug='bookings')
    ctx.update({
        'booking': booking,
        'travelers': booking.travelers.all(),
        'payments': booking.payments.all(),
        'documents': booking.documents.all(),
        'title': f"Booking {booking.booking_number}",
    })
    return render(request, 'manage/booking_detail.html', ctx)


@staff_required
def order_list(request):
    qs = Order.objects.select_related('user').order_by('-created_at')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(Q(user__username__icontains=query) | Q(id__icontains=query))
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='orders')
    ctx.update({'page_obj': page_obj, 'query': query, 'title': 'Shop Orders'})
    return render(request, 'manage/order_list.html', ctx)


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = status
            order.save()
            messages.success(request, "Order status updated.")
        return redirect('manage:order_detail', pk=pk)
    ctx = _base_context(request, active_slug='orders')
    ctx.update({'order': order, 'items': order.items.select_related('product').all(),
                 'title': f"Order #{order.id}"})
    return render(request, 'manage/order_detail.html', ctx)


@staff_required
def inquiry_list(request):
    qs = Inquiry.objects.order_by('is_resolved', '-created_at')
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='inquiries')
    ctx.update({'page_obj': page_obj, 'title': 'Customer Enquiries'})
    return render(request, 'manage/inquiry_list.html', ctx)


@staff_required
@require_POST
def inquiry_toggle_resolved(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    inquiry.is_resolved = not inquiry.is_resolved
    inquiry.save()
    messages.success(request, "Enquiry updated.")
    return redirect('manage:inquiries')


@staff_required
def review_list(request):
    qs = Review.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='reviews')
    ctx.update({'page_obj': page_obj, 'title': 'Customer Reviews'})
    return render(request, 'manage/review_list.html', ctx)


@staff_required
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, "Review removed.")
    return redirect('manage:reviews')


@staff_required
def newsletter_list(request):
    qs = NewsletterSubscriber.objects.order_by('-subscribed_at')
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='newsletter')
    ctx.update({'page_obj': page_obj, 'title': 'Newsletter Subscribers'})
    return render(request, 'manage/newsletter_list.html', ctx)


@staff_required
@require_POST
def newsletter_delete(request, pk):
    sub = get_object_or_404(NewsletterSubscriber, pk=pk)
    sub.delete()
    messages.success(request, "Subscriber removed.")
    return redirect('manage:newsletter')


# ── STAFF EMAIL ACCOUNTS (real cPanel mailboxes, not a DB model) ───────

@superuser_required
def staff_email_list(request):
    from . import cpanel_email
    ctx = _base_context(request, active_slug='staff-emails')
    try:
        mailboxes = cpanel_email.list_mailboxes()
        ctx['mailboxes'] = mailboxes
        ctx['unavailable'] = None
    except cpanel_email.CpanelUnavailable as e:
        ctx['mailboxes'] = []
        ctx['unavailable'] = str(e)
    except cpanel_email.CpanelError as e:
        ctx['mailboxes'] = []
        messages.error(request, f"Couldn't load mailboxes: {e}")
    ctx['domain'] = cpanel_email.COMPANY_EMAIL_DOMAIN
    ctx['title'] = 'Staff Emails'
    return render(request, 'manage/staff_email_list.html', ctx)


@superuser_required
def staff_email_add(request):
    from . import cpanel_email
    ctx = _base_context(request, active_slug='staff-emails')
    ctx['domain'] = cpanel_email.COMPANY_EMAIL_DOMAIN
    ctx['title'] = 'Add Staff Email'
    if request.method == 'POST':
        local_part = request.POST.get('local_part', '').strip().lower()
        quota_mb = request.POST.get('quota_mb', '1024').strip() or '1024'
        try:
            password = cpanel_email.generate_password()
            cpanel_email.create_mailbox(local_part, password, quota_mb=quota_mb)
            ctx['created_email'] = f"{local_part}@{cpanel_email.COMPANY_EMAIL_DOMAIN}"
            ctx['created_password'] = password
            return render(request, 'manage/staff_email_created.html', ctx)
        except cpanel_email.CpanelUnavailable as e:
            messages.error(request, str(e))
        except cpanel_email.CpanelError as e:
            messages.error(request, f"Couldn't create mailbox: {e}")
    return render(request, 'manage/staff_email_add.html', ctx)


@superuser_required
def staff_email_delete(request, email):
    from . import cpanel_email
    ctx = _base_context(request, active_slug='staff-emails')
    ctx['email'] = email
    ctx['title'] = 'Delete Staff Email'
    if request.method == 'POST':
        try:
            cpanel_email.delete_mailbox(email)
            messages.success(request, f'"{email}" was deleted.')
        except (cpanel_email.CpanelUnavailable, cpanel_email.CpanelError) as e:
            messages.error(request, f"Couldn't delete mailbox: {e}")
        return redirect('manage:staff_emails')
    return render(request, 'manage/staff_email_delete.html', ctx)


@superuser_required
def staff_email_reset_password(request, email):
    from . import cpanel_email
    ctx = _base_context(request, active_slug='staff-emails')
    ctx['email'] = email
    ctx['title'] = 'Reset Mailbox Password'
    if request.method == 'POST':
        try:
            password = cpanel_email.generate_password()
            cpanel_email.set_mailbox_password(email, password)
            ctx['created_email'] = email
            ctx['created_password'] = password
            return render(request, 'manage/staff_email_created.html', ctx)
        except (cpanel_email.CpanelUnavailable, cpanel_email.CpanelError) as e:
            messages.error(request, f"Couldn't reset password: {e}")
            return redirect('manage:staff_emails')
    return render(request, 'manage/staff_email_reset_password.html', ctx)
