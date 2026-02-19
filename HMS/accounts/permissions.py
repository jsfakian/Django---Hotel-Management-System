"""
Role-based access control utilities and decorators.
This module provides decorators and utilities for enforcing role-based permissions.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


# Define role hierarchy and permissions
ROLE_PERMISSIONS = {
    'admin': [
        'view_analytics',
        'view_operational_dashboard',
        'view_revenue_analytics',
        'view_guest_analytics',
        'view_reports',
        'export_analytics',
        'generate_analytics',
        'manage_users',
        'manage_properties',
        'manage_bookings',
        'manage_payments',
        'manage_staff',
        'generate_reports',
        'manage_contracts',
        'delete_records',
        'configure_system',
    ],
    'manager': [
        'view_analytics',
        'view_operational_dashboard',
        'view_revenue_analytics',
        'view_guest_analytics',
        'view_reports',
        'export_analytics',
        'view_property_analytics',
        'manage_bookings',
        'manage_room_services',
        'manage_staff',
        'generate_reports',
        'approve_refunds',
        'view_contracts',
    ],
    'receptionist': [
        'view_operational_dashboard',
        'view_bookings',
        'create_bookings',
        'modify_bookings',
        'view_guests',
        'process_payments',
        'handle_checkin_checkout',
        'manage_room_services',
    ],
    'staff': [
        'view_assigned_tasks',
        'view_operational_dashboard',
        'manage_room_services',
        'update_room_status',
        'view_guest_info',
    ],
    'guest': [
        'view_own_bookings',
        'create_bookings',
        'cancel_bookings',
        'request_services',
        'manage_account',
        'view_invoices',
    ],
}

# Role hierarchy (higher level can perform lower level actions)
ROLE_HIERARCHY = {
    'admin': ['manager', 'receptionist', 'staff', 'guest'],
    'manager': ['receptionist', 'staff', 'guest'],
    'receptionist': ['staff', 'guest'],
    'staff': ['guest'],
    'guest': [],
}


def get_user_role(user):
    """
    Get the primary role of a user.
    Returns the role name or None if user has no role.
    """
    if not user.is_authenticated:
        return None
    
    try:
        group = user.groups.first()
        return group.name if group else None
    except Exception:
        return None


def has_permission(user, permission):
    """
    Check if a user has a specific permission.
    """
    role = get_user_role(user)
    
    if not role:
        return False
    
    # Admin has all permissions
    if role == 'admin':
        return True
    
    # Check if role has permission
    role_perms = ROLE_PERMISSIONS.get(role, [])
    if permission in role_perms:
        return True
    
    return False


def has_role(user, *required_roles):
    """
    Check if user has one of the required roles.
    Respects role hierarchy (higher roles can perform lower role tasks).
    """
    if not user.is_authenticated:
        return False
    
    user_role = get_user_role(user)
    
    if not user_role:
        return False
    
    # Admin role can do everything
    if user_role == 'admin':
        return True
    
    # Check if user role matches or is higher in hierarchy
    for required_role in required_roles:
        if user_role == required_role:
            return True
        
        # Check role hierarchy
        lower_roles = ROLE_HIERARCHY.get(user_role, [])
        if required_role in lower_roles:
            return True
    
    return False


def require_role(*roles):
    """
    Decorator to require specific roles for a view.
    Supports role hierarchy.
    
    Usage:
        @require_role('admin', 'manager')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if has_role(request.user, *roles):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    f'You do not have permission to access this page. Required roles: {", ".join(roles)}'
                )
                return redirect('home')
        return wrapper
    return decorator


def require_permission(permission):
    """
    Decorator to require specific permission for a view.
    
    Usage:
        @require_permission('manage_properties')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url='login')
        def wrapper(request, *args, **kwargs):
            if has_permission(request.user, permission):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request,
                    f'You do not have permission to access this page. Required permission: {permission}'
                )
                return redirect('home')
        return wrapper
    return decorator


def check_object_access(user, obj, required_role='admin'):
    """
    Check if user has access to a specific object.
    For resources owned by users/managers, checks ownership.
    """
    user_role = get_user_role(user)
    
    if not user_role:
        return False
    
    # Admin can access everything
    if user_role == 'admin':
        return True
    
    # Check if object has a manager/owner field
    if hasattr(obj, 'manager') and obj.manager == user:
        return True
    
    if hasattr(obj, 'owner') and obj.owner == user:
        return True
    
    if hasattr(obj, 'user') and obj.user == user:
        return True
    
    # Check for guest-specific access
    if user_role == 'guest' and hasattr(obj, 'guest'):
        from accounts.models import Guest
        try:
            guest = Guest.objects.get(user=user)
            return obj.guest == guest
        except Guest.DoesNotExist:
            return False
    
    return False


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access across the application.
    """
    
    # URLs that don't require authentication
    OPEN_URLS = [
        '/login/',
        '/register/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if URL is open (no auth required)
        is_open_url = any(request.path.startswith(url) for url in self.OPEN_URLS)
        
        if not is_open_url and not request.user.is_authenticated:
            # Will be caught by @login_required decorators
            pass
        
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Add role information to request for use in views and templates.
        """
        if request.user.is_authenticated:
            request.user_role = get_user_role(request.user)
            request.user_permissions = set(ROLE_PERMISSIONS.get(request.user_role, []))
        else:
            request.user_role = None
            request.user_permissions = set()
        
        return None
