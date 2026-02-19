from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from accounts.permissions import get_user_role
from .models import Notification, NotificationPreference
from .services import NotificationService


@login_required(login_url='login')
@require_http_methods(["GET"])
def notification_list(request):
    """View user's notifications"""
    role = get_user_role(request.user)
    
    # Get notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        notifications = notifications.filter(status=status)
    
    # Get unread count
    unread_count = notifications.filter(status='unread').count()
    
    context = {
        'role': role,
        'notifications': notifications,
        'unread_count': unread_count,
        'status_filter': status,
    }
    
    return render(request, 'common_pages/notifications-list.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def mark_as_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    NotificationService.mark_as_read(notification)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Notification marked as read'
        })
    
    return redirect('notification-list')


@login_required(login_url='login')
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """Mark all notifications as read"""
    notifications = Notification.objects.filter(user=request.user, status='unread')
    
    for notification in notifications:
        NotificationService.mark_as_read(notification)
    
    count = notifications.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'{count} notifications marked as read'
        })
    
    messages.success(request, f'{count} notifications marked as read')
    return redirect('notification-list')


@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_notification(request, notification_id):
    """Delete/archive notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    NotificationService.delete_notification(notification)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Notification deleted'
        })
    
    return redirect('notification-list')


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def notification_preferences(request):
    """Manage notification preferences"""
    role = get_user_role(request.user)
    
    # Get or create preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.receive_in_app = request.POST.get('receive_in_app') == 'on'
        preferences.receive_email = request.POST.get('receive_email') == 'on'
        preferences.receive_sms = request.POST.get('receive_sms') == 'on'
        
        preferences.email_frequency = request.POST.get('email_frequency', 'daily')
        preferences.sms_frequency = request.POST.get('sms_frequency', 'never')
        
        preferences.booking_notifications = request.POST.get('booking_notifications') == 'on'
        preferences.payment_notifications = request.POST.get('payment_notifications') == 'on'
        preferences.service_notifications = request.POST.get('service_notifications') == 'on'
        preferences.event_notifications = request.POST.get('event_notifications') == 'on'
        preferences.system_notifications = request.POST.get('system_notifications') == 'on'
        preferences.promotional_notifications = request.POST.get('promotional_notifications') == 'on'
        
        preferences.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
        
        if preferences.quiet_hours_enabled:
            preferences.quiet_hours_start = request.POST.get('quiet_hours_start')
            preferences.quiet_hours_end = request.POST.get('quiet_hours_end')
        
        preferences.save()
        
        messages.success(request, 'Notification preferences updated successfully')
        return redirect('notification-preferences')
    
    context = {
        'role': role,
        'preferences': preferences,
    }
    
    return render(request, 'common_pages/notification-preferences.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def get_unread_count(request):
    """Get unread notification count (API)"""
    unread_count = Notification.objects.filter(
        user=request.user,
        status='unread'
    ).count()
    
    return JsonResponse({
        'unread_count': unread_count
    })


@login_required(login_url='login')
@require_http_methods(["GET"])
def get_recent_notifications(request):
    """Get recent notifications (API)"""
    limit = int(request.GET.get('limit', 5))
    
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:limit]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'status': n.status,
                'priority': n.priority,
                'icon': n.icon,
                'created_at': n.created_at.isoformat(),
                'action_url': n.action_url,
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)
