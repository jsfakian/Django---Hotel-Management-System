"""
Inventory Management Models

Centralized availability management (Nephele) for multi-channel synchronization.
Tracks room availability across all booking sources and channels.

Per DELIVERABLES-Task4-SystemArchitecture.md - Centralized Inventory Management
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class RoomAvailability(models.Model):
    """
    Centralized room availability record.
    Single source of truth for room availability across all channels and booking sources.
    One record per room per date.
    """
    
    # Room and date
    room = models.ForeignKey(
        'room.Room',
        on_delete=models.CASCADE,
        related_name='availability_records'
    )
    date = models.DateField(
        help_text="Date for this availability record"
    )
    
    # Availability units
    total_units = models.PositiveIntegerField(
        default=1,
        help_text="Total rooms available on this date"
    )
    available_units = models.PositiveIntegerField(
        default=1,
        help_text="Number of rooms available for booking"
    )
    booked_units = models.PositiveIntegerField(
        default=0,
        help_text="Number of rooms already booked"
    )
    blocked_units = models.PositiveIntegerField(
        default=0,
        help_text="Number of rooms blocked (maintenance, cleaning, etc.)"
    )
    overbooked_units = models.PositiveIntegerField(
        default=0,
        help_text="Number of rooms overbooked (staff override)"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base price per night"
    )
    dynamic_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dynamic price per night (from pricing engine)"
    )
    
    # Notes and tracking
    notes = models.TextField(
        blank=True,
        help_text="Notes about availability (e.g., reason for blocking)"
    )
    staff_override = models.BooleanField(
        default=False,
        help_text="True if manually set by staff"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='availability_updates',
        help_text="User who made the last update"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['room', 'date']
        indexes = [
            models.Index(fields=['room', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['available_units']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['room', 'date'],
                name='unique_room_availability_per_date'
            )
        ]
    
    def __str__(self):
        return f"{self.room.room_number} - {self.date}: {self.available_units} available"
    
    @property
    def is_available(self):
        """Check if any units are available"""
        return self.available_units > 0
    
    @property
    def occupancy_rate(self):
        """Calculate occupancy percentage"""
        if self.total_units == 0:
            return 0
        return (self.booked_units / self.total_units) * 100


class AvailabilitySyncLog(models.Model):
    """
    Log of availability synchronization attempts with external channels.
    Tracks success/failure for troubleshooting and monitoring.
    """
    
    SYNC_TYPE_CHOICES = (
        ('full_sync', 'Full Synchronization'),
        ('incremental_sync', 'Incremental Sync'),
        ('date_range', 'Date Range Sync'),
    )
    
    SYNC_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retry Scheduled'),
    )
    
    # References
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='availability_sync_logs'
    )
    channel = models.ForeignKey(
        'channels.Channel',
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    
    # Sync details
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        help_text="Type of synchronization"
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='pending',
        help_text="Current status of this sync"
    )
    
    # Scope
    rooms_affected = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of rooms affected by this sync"
    )
    date_from = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for range syncs"
    )
    date_to = models.DateField(
        null=True,
        blank=True,
        help_text="End date for range syncs"
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sync failed"
    )
    attempt_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of attempts for this sync"
    )
    
    # Response from channel
    response_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP status code from channel API"
    )
    response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full response data from channel API"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When sync completed or failed"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to retry if failed"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'sync_status']),
            models.Index(fields=['channel', 'sync_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.channel.get_channel_name_display()} - {self.get_sync_type_display()} ({self.get_sync_status_display()})"
