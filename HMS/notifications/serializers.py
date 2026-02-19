"""
Serializers for notifications app models

Per Task 4: Notification System & Communication
"""

from rest_framework import serializers
from notifications.models import (
    NotificationType, Notification, EmailNotification, SMSNotification
)


class NotificationTypeSerializer(serializers.ModelSerializer):
    """Serializer for NotificationType model"""
    
    class Meta:
        model = NotificationType
        fields = [
            'id', 'code', 'name', 'description', 'email_template',
            'sms_template', 'in_app_template', 'is_active'
        ]
        read_only_fields = ['id']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    notification_type_name = serializers.CharField(
        source='notification_type.name', read_only=True
    )
    is_new = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'notification_type',
            'notification_type_name', 'title', 'message', 'icon',
            'status', 'priority', 'action_url', 'action_label',
            'created_at', 'read_at', 'expires_at', 'is_new'
        ]
        read_only_fields = [
            'id', 'created_at', 'expires_at', 'is_new'
        ]

    def get_is_new(self, obj) -> bool:
        return obj.is_new()


class EmailNotificationSerializer(serializers.ModelSerializer):
    """Serializer for EmailNotification model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = EmailNotification
        fields = [
            'id', 'notification', 'user', 'user_name',
            'subject', 'body', 'recipient_email', 'status',
            'sent_at', 'opened_at', 'failed_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'sent_at', 'opened_at'
        ]


class SMSNotificationSerializer(serializers.ModelSerializer):
    """Serializer for SMSNotification model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = SMSNotification
        fields = [
            'id', 'notification', 'user', 'user_name',
            'message', 'phone_number', 'status', 'sent_at',
            'delivered_at', 'failed_reason', 'external_message_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sent_at', 'delivered_at']


class NotificationDetailedSerializer(NotificationSerializer):
    """Extended notification serializer with email/SMS data"""
    
    email_notification = EmailNotificationSerializer(read_only=True, allow_null=True)
    sms_notification = SMSNotificationSerializer(read_only=True, allow_null=True)
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'email_notification', 'sms_notification'
        ]
