from django.contrib import admin
from .models import (
    NotificationType, Notification, EmailNotification, SMSNotification,
    NotificationPreference, NotificationLog
)


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'notification_type', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'read_at']
    fieldsets = (
        ('Notification Info', {
            'fields': ('user', 'notification_type', 'title', 'message', 'icon')
        }),
        ('Status', {
            'fields': ('status', 'priority')
        }),
        ('Action', {
            'fields': ('action_url', 'action_label')
        }),
        ('Dates', {
            'fields': ('created_at', 'read_at', 'expires_at')
        }),
    )


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['subject', 'recipient_email', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'recipient_email', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'opened_at']


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'message', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['phone_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'receive_in_app', 'receive_email', 'receive_sms']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Channels', {
            'fields': ('receive_in_app', 'receive_email', 'receive_sms')
        }),
        ('Frequencies', {
            'fields': ('email_frequency', 'sms_frequency')
        }),
        ('Notification Types', {
            'fields': (
                'booking_notifications',
                'payment_notifications',
                'service_notifications',
                'event_notifications',
                'system_notifications',
                'promotional_notifications'
            )
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['notification__title']
    readonly_fields = ['timestamp']
