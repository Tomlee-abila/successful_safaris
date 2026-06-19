from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from inventory.models import Permission

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
                return redirect('dashboard')
        return _wrapped_view
    return decorator
