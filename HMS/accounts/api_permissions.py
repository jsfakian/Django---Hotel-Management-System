"""
DRF permission classes wired to accounts.permissions ROLE_PERMISSIONS.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import get_user_role, has_permission


STAFF_ROLES = frozenset({'admin', 'manager', 'receptionist', 'staff'})
MANAGEMENT_ROLES = frozenset({'admin', 'manager'})


def is_hotel_staff(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return get_user_role(user) in STAFF_ROLES


class IsHotelStaff(BasePermission):
    """Authenticated users in hotel staff groups (or superuser)."""

    def has_permission(self, request, view):
        return is_hotel_staff(request.user)


class IsManagement(BasePermission):
    """Admin or manager (or superuser)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return get_user_role(request.user) in MANAGEMENT_ROLES


class HasRolePermission(BasePermission):
    """
    Require a named permission from ROLE_PERMISSIONS.

    Set on a view/viewset:
        required_permission = 'manage_users'
        required_permission_map = {'create': 'manage_bookings', 'list': 'view_bookings'}
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        perm_map = getattr(view, 'required_permission_map', None) or {}
        action = getattr(view, 'action', None) or request.method.lower()
        permission = perm_map.get(action) or getattr(view, 'required_permission', None)

        if permission is None:
            # Default: staff for unsafe methods, any authenticated for SAFE
            if request.method in SAFE_METHODS:
                return True
            return is_hotel_staff(request.user)

        return has_permission(request.user, permission)
