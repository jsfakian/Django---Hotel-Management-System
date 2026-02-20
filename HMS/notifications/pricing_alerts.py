"""
Pricing Notification System

Sends real-time alerts to managers for pricing events:
1. Low confidence pricing predictions
2. Unusual price changes
3. Daily pricing summary reports
4. Performance alerts
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from bookings.models import PricingHistory


class PricingAlert(models.Model):
    """
    Stores pricing-related alerts for managers.
    """
    
    ALERT_TYPES = [
        ('low_confidence', 'Low Confidence Price'),
        ('high_deviation', 'High Price Deviation'),
        ('model_error', 'Model Error'),
        ('data_quality', 'Data Quality Issue'),
        ('performance', 'Performance Metric'),
        ('summary', 'Daily Summary'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Informational'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related data
    room = models.ForeignKey(
        'room.Room',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pricing_alerts'
    )
    pricing_history = models.ForeignKey(
        PricingHistory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    
    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pricing_alerts'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_pricing_alerts'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_alert_type_display()})"
    
    def mark_as_read(self):
        """Mark alert as read by recipient."""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def acknowledge(self, user):
        """Acknowledge alert with optional user note."""
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(update_fields=['is_acknowledged', 'acknowledged_at', 'acknowledged_by'])


class PricingAlertPreference(models.Model):
    """
    User preferences for pricing alerts.
    """
    
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate (as it happens)'),
        ('hourly', 'Hourly digest'),
        ('daily', 'Daily digest'),
        ('weekly', 'Weekly digest'),
        ('never', 'Never'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pricing_alert_preferences'
    )
    
    # Alert type preferences
    alert_low_confidence = models.BooleanField(default=True)
    alert_high_deviation = models.BooleanField(default=True)
    alert_model_errors = models.BooleanField(default=True)
    alert_data_quality = models.BooleanField(default=False)
    alert_performance = models.BooleanField(default=False)
    alert_summary = models.BooleanField(default=True)
    
    # Delivery preferences
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily'
    )
    
    # Severity threshold
    min_severity = models.CharField(
        max_length=10,
        choices=PricingAlert.SEVERITY_LEVELS,
        default='info',
        help_text='Only show alerts at this severity level or higher'
    )
    
    # Channels
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text='Start of quiet period (HH:MM in user timezone)'
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text='End of quiet period (HH:MM in user timezone)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Pricing alert preferences'
    
    def __str__(self):
        return f"Alert preferences for {self.user.get_full_name() or self.user.username}"
    
    @property
    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        current_time = timezone.now().time()
        return self.quiet_hours_start <= current_time <= self.quiet_hours_end


class PricingAlertLog(models.Model):
    """
    Audit log of all pricing alert actions.
    """
    
    ACTION_CHOICES = [
        ('created', 'Alert Created'),
        ('sent_email', 'Email Sent'),
        ('marked_read', 'Marked Read'),
        ('acknowledged', 'Acknowledged'),
        ('dismissed', 'Dismissed'),
    ]
    
    alert = models.ForeignKey(
        PricingAlert,
        on_delete=models.CASCADE,
        related_name='action_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Pricing alert logs'
    
    def __str__(self):
        return f"{self.alert} - {self.get_action_display()}"


# Signal handlers for automatic alert creation

@receiver(post_save, sender=PricingHistory)
def create_low_confidence_alert(sender, instance, created, **kwargs):
    """
    Automatically create alert when low-confidence pricing is recorded.
    """
    if not created:
        return
    
    # Check if confidence is low (< 80%)
    if instance.confidence_score and float(instance.confidence_score) < 0.80:
        managers = User.objects.filter(groups__name='Manager', is_active=True)
        
        for manager in managers:
            # Check if user wants these alerts
            prefs = getattr(manager, 'pricing_alert_preferences', None)
            if prefs and not prefs.alert_low_confidence:
                continue
            
            alert = PricingAlert.objects.create(
                alert_type='low_confidence',
                severity='warning',
                title=f"Low Confidence: {instance.room.name}",
                message=(
                    f"Pricing prediction for {instance.room.name} on {instance.date} "
                    f"has low confidence ({float(instance.confidence_score):.1%}). "
                    f"Recommended price: ${instance.dynamic_price:.2f}. "
                    f"Please review before applying."
                ),
                room=instance.room,
                pricing_history=instance,
                recipient=manager,
                severity='warning' if float(instance.confidence_score) >= 0.70 else 'critical'
            )
            
            # Send email if enabled
            if prefs and prefs.email_enabled:
                send_pricing_alert_email.delay(alert.id)


def send_pricing_alert_email(alert_id):
    """
    Send email notification for pricing alert.
    This would be a Celery task in production.
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        alert = PricingAlert.objects.get(id=alert_id)
        prefs = alert.recipient.pricing_alert_preferences
        
        # Check quiet hours
        if prefs.is_in_quiet_hours and prefs.quiet_hours_enabled:
            return False
        
        # Render email template
        context = {
            'alert': alert,
            'recipient': alert.recipient,
        }
        
        subject = f"[Pricing Alert] {alert.title}"
        
        # Plain text
        message = render_to_string('pricing/alerts/email_alert.txt', context)
        
        # HTML (optional)
        html_message = render_to_string('pricing/alerts/email_alert.html', context)
        
        # Send email
        send_mail(
            subject,
            message,
            'pricing-alerts@hotelms.local',
            [alert.recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Log action
        PricingAlertLog.objects.create(
            alert=alert,
            action='sent_email',
            details={'email': alert.recipient.email}
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send pricing alert email: {e}")
        return False


# Admin site registration

from django.contrib import admin

@admin.register(PricingAlert)
class PricingAlertAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'alert_type_badge',
        'severity_badge',
        'room_name',
        'recipient_name',
        'is_read_badge',
        'is_acknowledged_badge',
        'created_at',
    )
    list_filter = ('alert_type', 'severity', 'is_read', 'is_acknowledged', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'room__name')
    readonly_fields = ('created_at', 'updated_at', 'acknowledged_at')
    
    fieldsets = (
        ('Alert Info', {
            'fields': ('title', 'message', 'alert_type', 'severity'),
        }),
        ('Related Data', {
            'fields': ('room', 'pricing_history'),
        }),
        ('Recipient & Status', {
            'fields': ('recipient', 'is_read', 'is_acknowledged', 'acknowledged_by'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'acknowledged_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'acknowledge_alerts']
    
    def alert_type_badge(self, obj):
        """Display alert type with color badge."""
        colors = {
            'low_confidence': '#ff9800',
            'high_deviation': '#f44336',
            'model_error': '#f44336',
            'data_quality': '#ff9800',
            'performance': '#4caf50',
            'summary': '#2196F3',
        }
        return f'<span style="background-color: {colors.get(obj.alert_type, "#ccc")}; color: white; padding: 2px 8px; border-radius: 3px;">{obj.get_alert_type_display()}</span>'
    alert_type_badge.short_description = 'Type'
    alert_type_badge.allow_tags = True
    
    def severity_badge(self, obj):
        """Display severity with color."""
        colors = {'info': '#2196F3', 'warning': '#ff9800', 'critical': '#f44336'}
        return f'<span style="background-color: {colors.get(obj.severity, "#ccc")}; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">{obj.get_severity_display()}</span>'
    severity_badge.short_description = 'Severity'
    severity_badge.allow_tags = True
    
    def room_name(self, obj):
        return obj.room.name if obj.room else '-'
    room_name.short_description = 'Room'
    
    def recipient_name(self, obj):
        return obj.recipient.get_full_name() or obj.recipient.username
    recipient_name.short_description = 'Recipient'
    
    def is_read_badge(self, obj):
        return '✓ Read' if obj.is_read else '○ Unread'
    is_read_badge.short_description = 'Read Status'
    
    def is_acknowledged_badge(self, obj):
        return '✓ Acknowledged' if obj.is_acknowledged else '○ Not Acknowledged'
    is_acknowledged_badge.short_description = 'Acknowledged'
    
    def mark_as_read(self, request, queryset):
        count = queryset.update(is_read=True)
        self.message_user(request, f'{count} alerts marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        count = queryset.update(is_read=False)
        self.message_user(request, f'{count} alerts marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'
    
    def acknowledge_alerts(self, request, queryset):
        count = queryset.update(is_acknowledged=True, acknowledged_by=request.user, acknowledged_at=timezone.now())
        self.message_user(request, f'{count} alerts acknowledged.')
    acknowledge_alerts.short_description = 'Acknowledge selected alerts'


@admin.register(PricingAlertPreference)
class PricingAlertPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'frequency',
        'min_severity',
        'email_enabled_badge',
        'in_app_enabled_badge',
    )
    list_filter = ('frequency', 'min_severity', 'email_enabled', 'in_app_enabled')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('User', {
            'fields': ('user',),
        }),
        ('Alert Types', {
            'fields': (
                'alert_low_confidence',
                'alert_high_deviation',
                'alert_model_errors',
                'alert_data_quality',
                'alert_performance',
                'alert_summary',
            ),
        }),
        ('Delivery Settings', {
            'fields': ('frequency', 'min_severity', 'email_enabled', 'in_app_enabled'),
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'),
            'classes': ('collapse',),
        }),
    )
    
    def email_enabled_badge(self, obj):
        return '✓ Email' if obj.email_enabled else '○ No Email'
    email_enabled_badge.short_description = 'Email'
    
    def in_app_enabled_badge(self, obj):
        return '✓ In-App' if obj.in_app_enabled else '○ No In-App'
    in_app_enabled_badge.short_description = 'In-App'


@admin.register(PricingAlertLog)
class PricingAlertLogAdmin(admin.ModelAdmin):
    list_display = ('alert', 'action', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('alert__title', 'user__username')
    readonly_fields = ('created_at',)
