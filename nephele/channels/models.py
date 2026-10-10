"""
Channel Integration Models

Manages connections to external OTA platforms:
- Booking.com, Trivago, Airbnb, Expedia, Agoda, VRBO, etc.

Per DELIVERABLES-Task4-SystemArchitecture.md - Channel Integration System
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import json
import hashlib
import hmac


class Channel(models.Model):
    """
    Configuration for external OTA platform integration.
    Stores API credentials, room mappings, and synchronization settings.
    """
    
    CHANNEL_CHOICES = (
        ('booking_com', 'Booking.com'),
        ('trivago', 'Trivago'),
        ('airbnb', 'Airbnb'),
        ('expedia', 'Expedia'),
        ('agoda', 'Agoda'),
        ('vrbo', 'VRBO'),
        ('booking_buddy', 'Booking Buddy'),
        ('hotwire', 'Hotwire'),
        ('travelocity', 'Travelocity'),
        ('priceline', 'Priceline'),
        ('orbitz', 'Orbitz'),
        ('kayak', 'Kayak'),
        ('hostelworld', 'HostelWorld'),
        ('ctrip', 'Ctrip'),
        ('custom', 'Custom OTA'),
    )
    
    CHANNEL_TYPE_CHOICES = (
        ('ota', 'Online Travel Agency'),
        ('metasearch', 'Metasearch Engine'),
        ('direct', 'Direct Booking'),
    )
    
    # Property and channel info
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='channels'
    )
    channel_name = models.CharField(
        max_length=50,
        choices=CHANNEL_CHOICES,
        help_text="OTA platform name"
    )
    channel_type = models.CharField(
        max_length=50,
        choices=CHANNEL_TYPE_CHOICES,
        default='ota'
    )
    
    # API Credentials (encrypted in production)
    account_id = models.CharField(
        max_length=255,
        help_text="Channel account ID or username"
    )
    api_key = models.CharField(
        max_length=500,
        help_text="API key for authentication"
    )
    api_secret = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional API secret for webhook signing"
    )
    
    # Synchronization Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this channel"
    )
    sync_enabled = models.BooleanField(
        default=True,
        help_text="Sync availability to this channel"
    )
    accept_bookings = models.BooleanField(
        default=True,
        help_text="Accept incoming bookings from this channel"
    )
    
    # Room and Rate Mappings
    mapping_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Configuration for mapping NEPHELE room IDs to channel room IDs.
        Format: {
            "room_mappings": {"123": "channel_room_id"},
            "rate_mappings": {"123": "rate_code"},
            "sync_overrides": {...}
        }
        """
    )
    
    # Sync Tracking
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful synchronization timestamp"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message from channel API"
    )
    error_count = models.IntegerField(
        default=0,
        help_text="Number of consecutive sync failures"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['property', 'channel_name']
        indexes = [
            models.Index(fields=['property', 'is_active']),
            models.Index(fields=['channel_name']),
            models.Index(fields=['last_sync_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['property', 'channel_name'],
                name='unique_channel_per_property'
            )
        ]
    
    def __str__(self):
        return f"{self.get_channel_name_display()} - {self.property.name}"
    
    def get_readable_api_key(self):
        """Return masked API key for display"""
        if len(self.api_key) > 8:
            return f"{self.api_key[:4]}...{self.api_key[-4:]}"
        return "★" * len(self.api_key)
    
    def verify_webhook_signature(self, payload, signature, secret=None):
        """
        Verify HMAC-SHA256 signature of webhook payload.
        
        Args:
            payload: Request body (string or bytes)
            signature: Provided signature (hex format)
            secret: Secret key (uses api_secret if None)
        
        Returns:
            bool: True if signature is valid
        """
        secret_key = secret or self.api_secret
        if not secret_key:
            return False
        
        if isinstance(payload, str):
            payload = payload.encode()
        
        expected = hmac.new(
            secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)


class ChannelBooking(models.Model):
    """
    Track channel-specific booking references.
    Links external OTA booking IDs to internal NEPHELE booking IDs.
    Used for duplicate detection and sync state management.
    """
    
    SYNC_STATUS_CHOICES = (
        ('pending', 'Pending Sync'),
        ('synced', 'Synced'),
        ('failed', 'Sync Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Booking references
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='channel_bookings'
    )
    channel_booking_id = models.CharField(
        max_length=255,
        help_text="Booking ID from the external channel"
    )
    nephele_booking = models.ForeignKey(
        'room.Booking',
        on_delete=models.CASCADE,
        related_name='channel_bookings'
    )
    
    # Sync Status
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='synced'
    )
    
    # Channel-specific data (for reference)
    channel_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full booking data from channel"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['channel', 'channel_booking_id']),
            models.Index(fields=['nephele_booking']),
            models.Index(fields=['sync_status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'channel_booking_id'],
                name='unique_channel_booking'
            )
        ]
    
    def __str__(self):
        return f"{self.channel.get_channel_name_display()} - {self.channel_booking_id}"
