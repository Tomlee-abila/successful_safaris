from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from inventory.models import Permission


def shop_enabled_required(view_func):
    """Takes a shop view offline entirely while the shop is switched off in
    Site Settings — visiting the URL directly bounces to the homepage instead
    of rendering the page."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        from core.models import SiteSettings
        if not SiteSettings.get_solo().shop_enabled:
            messages.error(request, "Our shop is currently closed.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def permission_required(module_name, action='view'):
    """
    Decorator for views that checks whether a user has a particular permission 
    enabled in the inventory.Permission matrix.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Map Django groups to RBAC Roles
            role_map = {
                'Customer': 'USER',
                'Sub Admin': 'SUBADMIN',
                'Super Admin': 'SUPERADMIN',
            }
            
            if not request.user.is_authenticated:
                role = 'VISITOR'
            else:
                user_group = request.user.groups.first()
                group_name = user_group.name if user_group else 'Customer'
                role = role_map.get(group_name, 'USER')

            # Check the Permission matrix
            perm = Permission.objects.filter(
                module__name=module_name,
                role=role
            ).first()
            
            has_perm = False
            if perm:
                if action == 'view': has_perm = perm.can_view
                elif action == 'create': has_perm = perm.can_create
                elif action == 'edit': has_perm = perm.can_edit
                elif action == 'delete': has_perm = perm.can_delete
            
            if has_perm:
                return view_func(request, *args, **kwargs)
            else:
                if not request.user.is_authenticated:
                    return redirect('auth')
                messages.error(request, f"Access Denied: You do not have '{action}' permission for {module_name}.")
                # Redirect to 'home', not 'dashboard': if the denied view IS the
                # dashboard (e.g. the permission matrix is empty/misconfigured),
                # redirecting back to it would loop forever (ERR_TOO_MANY_REDIRECTS).
                return redirect('home')
        return _wrapped_view
    return decorator
