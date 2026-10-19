from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
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

from .models import ManagePermission
from .registry import SECTIONS, ALL_SECTION_CHOICES, ALL_SECTION_SLUGS


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
    content. Never delegable via section checkboxes."""
    @wraps(view_func)
    @staff_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Only a super admin can manage staff email accounts.")
            return redirect('manage:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped


def accessible_sections(user):
    """Full set of section slugs this user can use. Superusers always get
    everything; everyone else gets exactly what's been explicitly granted."""
    if user.is_superuser:
        return set(ALL_SECTION_SLUGS)
    return set(ManagePermission.objects.filter(user=user).values_list('section', flat=True))


def has_section_access(user, slug):
    return user.is_superuser or slug in accessible_sections(user)


def section_required(slug):
    """Gates a fixed (non-registry) view behind one checkbox-grantable
    section, e.g. @section_required('bookings')."""
    def decorator(view_func):
        @wraps(view_func)
        @staff_required
        def wrapped(request, *args, **kwargs):
            if not has_section_access(request.user, slug):
                messages.error(request, "You don't have access to that section.")
                return redirect('manage:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def _section_or_404(slug):
    section = SECTIONS.get(slug)
    if not section:
        raise Http404("Unknown section")
    return section


def _nav_groups(user):
    allowed = accessible_sections(user)
    groups = {}
    for slug, section in SECTIONS.items():
        if slug in allowed:
            groups.setdefault(section['group'], []).append((slug, section))
    return groups


def _base_context(request, active_slug=None):
    allowed = accessible_sections(request.user)
    return {
        'nav_groups': _nav_groups(request.user),
        'accessible_slugs': allowed,
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


@section_required('site-settings')
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
    if not has_section_access(request.user, slug):
        messages.error(request, "You don't have access to that section.")
        return redirect('manage:dashboard')
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
    if not has_section_access(request.user, slug):
        messages.error(request, "You don't have access to that section.")
        return redirect('manage:dashboard')
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
    if not has_section_access(request.user, slug):
        messages.error(request, "You don't have access to that section.")
        return redirect('manage:dashboard')
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
    if not has_section_access(request.user, slug):
        messages.error(request, "You don't have access to that section.")
        return redirect('manage:dashboard')
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


@section_required('bookings')
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


@section_required('bookings')
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


@section_required('orders')
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


@section_required('orders')
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


@section_required('inquiries')
def inquiry_list(request):
    qs = Inquiry.objects.order_by('is_resolved', '-created_at')
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='inquiries')
    ctx.update({'page_obj': page_obj, 'title': 'Customer Enquiries'})
    return render(request, 'manage/inquiry_list.html', ctx)


@section_required('inquiries')
@require_POST
def inquiry_toggle_resolved(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    inquiry.is_resolved = not inquiry.is_resolved
    inquiry.save()
    messages.success(request, "Enquiry updated.")
    return redirect('manage:inquiries')


@section_required('reviews')
def review_list(request):
    qs = Review.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='reviews')
    ctx.update({'page_obj': page_obj, 'title': 'Customer Reviews'})
    return render(request, 'manage/review_list.html', ctx)


@section_required('reviews')
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, "Review removed.")
    return redirect('manage:reviews')


@section_required('newsletter')
def newsletter_list(request):
    qs = NewsletterSubscriber.objects.order_by('-subscribed_at')
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    ctx = _base_context(request, active_slug='newsletter')
    ctx.update({'page_obj': page_obj, 'title': 'Newsletter Subscribers'})
    return render(request, 'manage/newsletter_list.html', ctx)


@section_required('newsletter')
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


# ── MY ACCOUNT (any staff — self-service password change) ──────────────

@staff_required
def my_account(request):
    ctx = _base_context(request, active_slug='account')
    ctx['title'] = 'My Account'
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep the user logged in
            messages.success(request, "Your password was changed.")
            return redirect('manage:account')
    else:
        form = PasswordChangeForm(request.user)
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-input'
    ctx['form'] = form
    return render(request, 'manage/account.html', ctx)


# ── STAFF USERS & ROLES ─────────────────────────────────────────────────
# Delegable like any other section (via 'staff-users'), but with hard
# power-dynamics guardrails that apply even to a non-superuser holding it:
# they can never touch a superuser's account, never edit themselves here,
# and can never grant another user more access than they themselves have.

@section_required('staff-users')
def staff_user_list(request):
    ctx = _base_context(request, active_slug='staff-users')
    ctx['title'] = 'Staff Users'
    rows = []
    for u in User.objects.filter(is_staff=True).order_by('username'):
        can_manage = u.pk != request.user.pk and (request.user.is_superuser or not u.is_superuser)
        rows.append((u, can_manage))
    ctx['staff_user_rows'] = rows
    return render(request, 'manage/staff_user_list.html', ctx)


def _can_manage_target(request, target):
    if target.pk == request.user.pk:
        messages.error(request, "Use My Account to manage your own password.")
        return False
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, "Only a Super Admin can manage another Super Admin's account.")
        return False
    return True


@section_required('staff-users')
def staff_user_permissions(request, pk):
    target = get_object_or_404(User, pk=pk, is_staff=True)
    if not _can_manage_target(request, target):
        return redirect('manage:staff_users')

    actor_sections = accessible_sections(request.user)
    editable_choices = (
        ALL_SECTION_CHOICES if request.user.is_superuser
        else [(slug, label) for slug, label in ALL_SECTION_CHOICES if slug in actor_sections]
    )
    current = accessible_sections(target)

    if request.method == 'POST':
        if request.user.is_superuser and 'is_superuser' in request.POST:
            target.is_superuser = request.POST.get('is_superuser') == 'on'
            target.save()
        checked = set(request.POST.getlist('sections'))
        for slug, _label in editable_choices:
            should_have = slug in checked
            exists = ManagePermission.objects.filter(user=target, section=slug).exists()
            if should_have and not exists:
                ManagePermission.objects.create(user=target, section=slug)
            elif not should_have and exists:
                ManagePermission.objects.filter(user=target, section=slug).delete()
        messages.success(request, f"Updated access for {target.username}.")
        return redirect('manage:staff_users')

    ctx = _base_context(request, active_slug='staff-users')
    ctx.update({
        'target': target,
        'editable_choices': editable_choices,
        'current': current,
        'limited': not request.user.is_superuser,
        'title': f"Manage Access — {target.username}",
    })
    return render(request, 'manage/staff_user_permissions.html', ctx)


@section_required('staff-users')
@require_POST
def staff_user_reset_password(request, pk):
    from .cpanel_email import generate_password
    target = get_object_or_404(User, pk=pk, is_staff=True)
    if not _can_manage_target(request, target):
        return redirect('manage:staff_users')

    password = generate_password()
    target.set_password(password)
    target.save()

    if target.email:
        try:
            send_mail(
                subject='Your Successful Luxury Safaris admin password was reset',
                message=(
                    f"Hi {target.first_name or target.username},\n\n"
                    "Your password for the website's Manage panel was just reset.\n\n"
                    f"New password: {password}\n\n"
                    "Please sign in and change it to something memorable from My Account."
                ),
                from_email=None,
                recipient_list=[target.email],
                fail_silently=False,
            )
            messages.success(request, f"New password emailed to {target.email}.")
            return redirect('manage:staff_users')
        except Exception as e:
            messages.error(request, f"Couldn't send the email ({e}) — showing it here instead.")
    else:
        messages.error(request, f"{target.username} has no email on file — showing the new password here instead.")

    ctx = _base_context(request, active_slug='staff-users')
    ctx.update({'created_email': target.username, 'created_password': password, 'title': 'Password Reset'})
    return render(request, 'manage/staff_user_password_reveal.html', ctx)
