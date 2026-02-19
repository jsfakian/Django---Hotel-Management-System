"""
Context processors for HMS application.
Provides common context variables for all templates.
"""

from .permissions import get_user_role, ROLE_PERMISSIONS


def user_context(request):
    """
    Add user role and permissions to template context.
    """
    context = {
        'user_role': None,
        'user_permissions': set(),
        'all_roles': list(ROLE_PERMISSIONS.keys()),
    }
    
    if request.user.is_authenticated:
        user_role = get_user_role(request.user)
        context['user_role'] = user_role
        context['user_permissions'] = set(ROLE_PERMISSIONS.get(user_role, []))
    
    return context
