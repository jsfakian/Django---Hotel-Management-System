"""
Notification service for sending notifications via multiple channels.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import (
    Notification, EmailNotification, SMSNotification,
    NotificationType, NotificationPreference, NotificationLog
)


class NotificationService:
    """
    Service class for creating and sending notifications
    """
    
    @staticmethod
    def send_notification(user, notification_type_code, title, message, 
                         action_url='', action_label='', priority='medium',
                         icon='', channels=None):
        """
        Create and send notification to user via specified channels
        
        Args:
            user: User instance
            notification_type_code: Code of NotificationType
            title: Notification title
            message: Notification message
            action_url: URL to navigate to on click
            action_label: Label for action button
            priority: Priority level (low, medium, high, urgent)
            icon: Icon class or emoji
            channels: List of channels to use (in_app, email, sms) or None for all
        
        Returns:
            Notification instance or None if failed
        """
        try:
            # Get notification type
            notification_type = NotificationType.objects.get(code=notification_type_code)
        except NotificationType.DoesNotExist:
            print(f"Notification type {notification_type_code} not found")
            return None
        
        # Get user preferences
        try:
            preferences = user.notification_preference
        except NotificationPreference.DoesNotExist:
            # Create default preferences if not exist
            preferences = NotificationPreference.objects.create(user=user)
        
        # Determine which channels to use
        if channels is None:
            channels = []
            if preferences.receive_in_app:
                channels.append('in_app')
            if preferences.receive_email and not preferences.is_in_quiet_hours():
                channels.append('email')
            if preferences.receive_sms and not preferences.is_in_quiet_hours():
                channels.append('sms')
        
        # Create in-app notification
        notification = None
        if 'in_app' in channels:
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                action_label=action_label,
                priority=priority,
                icon=icon
            )
            
            # Log creation
            NotificationLog.objects.create(
                notification=notification,
                action='create',
                details='In-app notification created'
            )
        
        # Send email notification
        if 'email' in channels:
            NotificationService.send_email(
                user, notification, title, message
            )
        
        # Send SMS notification
        if 'sms' in channels and hasattr(user, 'employee') and user.employee.phoneNumber:
            NotificationService.send_sms(
                user, notification, message
            )
        
        return notification
    
    @staticmethod
    def send_email(user, notification=None, subject='', body=''):
        """Send email notification"""
        try:
            if not user.email:
                return False
            
            email_notif = EmailNotification.objects.create(
                user=user,
                notification=notification,
                subject=subject,
                body=body,
                recipient_email=user.email
            )
            
            # Send email
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                email_notif.status = 'sent'
                email_notif.sent_at = timezone.now()
                email_notif.save()
                
                # Log
                if notification:
                    NotificationLog.objects.create(
                        notification=notification,
                        action='send',
                        details=f'Email sent to {user.email}'
                    )
                
                return True
            
            except Exception as e:
                email_notif.status = 'failed'
                email_notif.failed_reason = str(e)
                email_notif.save()
                
                if notification:
                    NotificationLog.objects.create(
                        notification=notification,
                        action='fail',
                        details=f'Email send failed: {str(e)}'
                    )
                
                return False
        
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def send_sms(user, notification=None, message=''):
        """
        Send SMS notification
        Note: Requires SMS gateway configuration (Twilio, etc.)
        """
        try:
            # This is a placeholder. Implement with actual SMS service
            # Example: Twilio, AWS SNS, etc.
            
            phone_number = getattr(user, 'phone_number', None)
            if not phone_number:
                return False
            
            sms_notif = SMSNotification.objects.create(
                user=user,
                notification=notification,
                message=message,
                phone_number=str(phone_number)
            )
            
            # TODO: Integrate with SMS gateway
            # For now, just mark as pending
            
            if notification:
                NotificationLog.objects.create(
                    notification=notification,
                    action='send',
                    details=f'SMS scheduled for {phone_number}'
                )
            
            return True
        
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False
    
    @staticmethod
    def mark_as_read(notification):
        """Mark notification as read"""
        notification.mark_as_read()
        
        NotificationLog.objects.create(
            notification=notification,
            action='read',
            details='Notification marked as read'
        )
    
    @staticmethod
    def delete_notification(notification):
        """Delete/archive notification"""
        notification.status = 'deleted'
        notification.save()
        
        NotificationLog.objects.create(
            notification=notification,
            action='delete',
            details='Notification deleted'
        )
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Clean up old notifications (older than specified days)
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count = 0
        for notification in Notification.objects.filter(created_at__lt=cutoff_date, status='deleted'):
            notification.delete()
            deleted_count += 1
        
        return deleted_count


# Helper functions for specific notification types

def notify_booking_created(booking):
    """Send notification for booking creation"""
    subject = f"Booking #{booking.id} Created"
    message = f"Your booking for room {booking.roomNumber.number} has been created. Check-in: {booking.startDate}, Check-out: {booking.endDate}"
    
    NotificationService.send_notification(
        user=booking.guest.user,
        notification_type_code='booking_created',
        title=subject,
        message=message,
        action_url=f'/bookings/{booking.id}/',
        action_label='View Booking',
        icon='📅'
    )


def notify_payment_received(payment):
    """Send notification for payment received"""
    subject = f"Payment Received - {payment.amount} {payment.currency}"
    message = f"Your payment of {payment.amount} {payment.currency} has been received successfully. Reference: {payment.reference_code}"
    
    NotificationService.send_notification(
        user=payment.guest.user,
        notification_type_code='payment_received',
        title=subject,
        message=message,
        action_url=f'/payments/history/',
        action_label='View Payment',
        priority='high',
        icon='✅'
    )


def notify_payment_failed(payment):
    """Send notification for payment failure"""
    subject = "Payment Failed"
    message = f"Your payment of {payment.amount} {payment.currency} could not be processed. Please try again or contact support."
    
    NotificationService.send_notification(
        user=payment.guest.user,
        notification_type_code='payment_failed',
        title=subject,
        message=message,
        action_url=f'/payments/process/{payment.booking.id}/',
        action_label='Retry Payment',
        priority='high',
        icon='❌'
    )


def notify_refund_processed(refund):
    """Send notification for refund processing"""
    subject = f"Refund Processed - {refund.refund_amount}"
    message = f"Your refund of {refund.refund_amount} has been processed. It should appear in your account within 3-5 business days."
    
    NotificationService.send_notification(
        user=refund.guest.user,
        notification_type_code='refund_processed',
        title=subject,
        message=message,
        action_url=f'/payments/refund-history/',
        action_label='View Refund',
        icon='💰'
    )


def notify_room_service_request(service_request):
    """Send notification for room service request"""
    subject = f"Room Service Request Received"
    message = f"Your {service_request.get_servicesType_display()} request has been received. We'll be with you shortly."
    
    NotificationService.send_notification(
        user=service_request.curBooking.guest.user,
        notification_type_code='room_service_request',
        title=subject,
        message=message,
        action_url=f'/room-services/',
        action_label='View Services',
        icon='🔔'
    )


def notify_checkin_reminder(booking):
    """Send check-in reminder notification"""
    subject = "Check-in Reminder"
    message = f"Your check-in is today! Your room is {booking.roomNumber.number}. Check-in time is 14:00."
    
    NotificationService.send_notification(
        user=booking.guest.user,
        notification_type_code='checkin_reminder',
        title=subject,
        message=message,
        action_url=f'/bookings/{booking.id}/',
        action_label='View Booking',
        priority='high',
        icon='🏨'
    )


def notify_checkout_reminder(booking):
    """Send check-out reminder notification"""
    subject = "Check-out Reminder"
    message = f"Your check-out is tomorrow. Check-out time is 11:00. Thank you for staying with us!"
    
    NotificationService.send_notification(
        user=booking.guest.user,
        notification_type_code='checkout_reminder',
        title=subject,
        message=message,
        action_url=f'/bookings/{booking.id}/',
        action_label='View Booking',
        icon='👋'
    )
