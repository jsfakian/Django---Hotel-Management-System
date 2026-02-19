from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class NotificationType(models.Model):
    """
    Notification types (Booking Confirmed, Payment Received, etc.)
    """
    CODE_CHOICES = [
        ('booking_created', 'Booking Created'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('booking_modified', 'Booking Modified'),
        ('payment_received', 'Payment Received'),
        ('payment_failed', 'Payment Failed'),
        ('payment_verified', 'Payment Verified'),
        ('refund_requested', 'Refund Requested'),
        ('refund_approved', 'Refund Approved'),
        ('refund_rejected', 'Refund Rejected'),
        ('refund_processed', 'Refund Processed'),
        ('room_service_request', 'Room Service Request'),
        ('room_service_completed', 'Room Service Completed'),
        ('checkin_reminder', 'Check-in Reminder'),
        ('checkout_reminder', 'Check-out Reminder'),
        ('invoice_generated', 'Invoice Generated'),
        ('invoice_overdue', 'Invoice Overdue'),
        ('event_created', 'Event Created'),
        ('event_updated', 'Event Updated'),
        ('event_cancelled', 'Event Cancelled'),
        ('maintenance_alert', 'Maintenance Alert'),
        ('system_alert', 'System Alert'),
    ]
    
    code = models.CharField(max_length=50, unique=True, choices=CODE_CHOICES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Notification settings
    email_template = models.CharField(max_length=100, blank=True)
    sms_template = models.CharField(max_length=100, blank=True)
    in_app_template = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Notification Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Notification(models.Model):
    """
    User notifications (in-app notifications)
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.ForeignKey(NotificationType, on_delete=models.PROTECT)
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Action link
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()
    
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    @property
    def is_new(self):
        """Check if notification is new (less than 1 hour old)"""
        return (timezone.now() - self.created_at).seconds < 3600


class EmailNotification(models.Model):
    """
    Email notification tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    # Relationships
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='email_notification'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_notifications')
    
    # Email details
    subject = models.CharField(max_length=200)
    body = models.TextField()
    recipient_email = models.EmailField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Email: {self.subject}"


class SMSNotification(models.Model):
    """
    SMS notification tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('undelivered', 'Undelivered'),
    ]
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_notifications')
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sms_notification'
    )
    
    # SMS details
    message = models.CharField(max_length=160)
    phone_number = models.CharField(max_length=20)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    
    # External reference
    external_message_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"SMS: {self.message[:50]}..."


class NotificationPreference(models.Model):
    """
    User notification preferences
    """
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('never', 'Never'),
    ]
    
    # Relationships
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Notification channels
    receive_in_app = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=True)
    receive_sms = models.BooleanField(default=False)
    
    # Frequency
    email_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    sms_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='never')
    
    # Notification types to receive
    booking_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    service_notifications = models.BooleanField(default=True)
    event_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    promotional_notifications = models.BooleanField(default=False)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # e.g., 08:00
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_in_quiet_hours(self):
        """Check if current time is in quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from datetime import datetime
        current_time = datetime.now().time()
        
        if self.quiet_hours_start > self.quiet_hours_end:
            # Quiet hours span midnight (e.g., 22:00 to 08:00)
            return current_time >= self.quiet_hours_start or current_time < self.quiet_hours_end
        else:
            # Quiet hours don't span midnight
            return self.quiet_hours_start <= current_time < self.quiet_hours_end


class NotificationLog(models.Model):
    """
    Log of all notification activities
    """
    USER_CHOICE = [
        ('create', 'Create'),
        ('send', 'Send'),
        ('read', 'Read'),
        ('delete', 'Delete'),
        ('bounce', 'Bounce'),
        ('fail', 'Fail'),
    ]
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=20, choices=USER_CHOICE)
    details = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Notification Logs"
    
    def __str__(self):
        return f"{self.notification.title} - {self.action}"
