# nephele/inventory/models.py
"""
Inventory Management Models

Centralized availability management (Nephele) for multi-channel synchronization.
Tracks room availability across all booking sources and channels.
"""

from django.contrib.auth.models import User
from django.db import models


class RoomAvailability(models.Model):
    """
    Centralized room availability record.
    Single source of truth for room availability across all channels and booking sources.
    One record per room per date.
    """

    room = models.ForeignKey(
        "room.Room",
        on_delete=models.CASCADE,
        related_name="availability_records",
    )
    date = models.DateField(help_text="Date for this availability record")

    total_units = models.PositiveIntegerField(
        default=1, help_text="Total rooms available on this date"
    )
    available_units = models.PositiveIntegerField(
        default=1, help_text="Number of rooms available for booking"
    )
    booked_units = models.PositiveIntegerField(
        default=0, help_text="Number of rooms already booked"
    )
    blocked_units = models.PositiveIntegerField(
        default=0,
        help_text="Number of rooms blocked (maintenance, cleaning, etc.)",
    )
    overbooked_units = models.PositiveIntegerField(
        default=0, help_text="Number of rooms overbooked (staff override)"
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Base price per night",
    )
    dynamic_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dynamic price per night (from pricing engine)",
    )

    notes = models.TextField(
        blank=True, help_text="Notes about availability (e.g., reason for blocking)"
    )
    staff_override = models.BooleanField(
        default=False, help_text="True if manually set by staff"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="availability_updates",
        help_text="User who made the last update",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room", "date"]
        indexes = [
            models.Index(fields=["room", "date"]),
            models.Index(fields=["date"]),
            models.Index(fields=["available_units"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "date"],
                name="unique_room_availability_per_date",
            )
        ]

    def __str__(self):
        return f"{self.room.room_number} - {self.date}: {self.available_units} available"

    @property
    def is_available(self):
        return self.available_units > 0

    @property
    def occupancy_rate(self):
        if self.total_units == 0:
            return 0
        return (self.booked_units / self.total_units) * 100


class AvailabilitySyncLog(models.Model):
    """Log of availability synchronization attempts with external channels."""

    SYNC_TYPE_CHOICES = (
        ("full_sync", "Full Synchronization"),
        ("incremental_sync", "Incremental Sync"),
        ("date_range", "Date Range Sync"),
    )

    SYNC_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("retry", "Retry Scheduled"),
        ("not_implemented", "Not Implemented"),
    )

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="availability_sync_logs",
    )
    channel = models.ForeignKey(
        "channels.Channel",
        on_delete=models.CASCADE,
        related_name="sync_logs",
    )

    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        help_text="Type of synchronization",
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default="pending",
        help_text="Current status of this sync",
    )

    rooms_affected = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of rooms affected by this sync",
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    error_message = models.TextField(blank=True)
    attempt_count = models.PositiveIntegerField(default=1)

    response_code = models.IntegerField(null=True, blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["property", "sync_status"]),
            models.Index(fields=["channel", "sync_status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.channel.get_channel_name_display()} - "
            f"{self.get_sync_type_display()} ({self.get_sync_status_display()})"
        )


class RoomType(models.Model):
    """Catalog room type for a property (sellable inventory unit type)."""

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="room_types",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=2)
    max_occupancy = models.PositiveIntegerField(default=2)
    base_occupancy = models.PositiveIntegerField(default=2)
    amenities = models.JSONField(default=list, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["property", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "code"],
                name="unique_room_type_code_per_property",
            )
        ]
        indexes = [
            models.Index(fields=["property", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class RatePlan(models.Model):
    """Rate plan attached to one or more room types."""

    MEAL_PLAN_CHOICES = (
        ("BB", "Bed & Breakfast"),
        ("HB", "Half Board"),
        ("FB", "Full Board"),
        ("RO", "Room Only"),
        ("AI", "All Inclusive"),
    )

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="rate_plans",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    meal_plan = models.CharField(
        max_length=2,
        choices=MEAL_PLAN_CHOICES,
        default="RO",
    )
    is_refundable = models.BooleanField(default=True)
    cancellation_policy = models.TextField(blank=True)
    room_types = models.ManyToManyField(
        RoomType,
        related_name="rate_plans",
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["property", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "code"],
                name="unique_rate_plan_code_per_property",
            )
        ]
        indexes = [
            models.Index(fields=["property", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class RoomTypeAvailability(models.Model):
    """Per-date allotment and restrictions for a room type."""

    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="availability_calendar",
    )
    date = models.DateField()
    allotment = models.PositiveIntegerField(default=0)
    booked = models.PositiveIntegerField(default=0)
    stop_sell = models.BooleanField(default=False)
    min_stay = models.PositiveIntegerField(
        default=1, null=True, blank=True, help_text="Minimum stay nights"
    )
    max_stay = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        help_text="0 means no maximum stay limit",
    )
    cta = models.BooleanField(default=False, help_text="Closed to arrival")
    ctd = models.BooleanField(default=False, help_text="Closed to departure")
    closed = models.BooleanField(default=False)
    staff_override = models.BooleanField(
        default=False,
        help_text="When True, automated allotment backfill will not overwrite this row",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="room_type_availability_updates",
    )
    restrictions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room_type", "date"]
        constraints = [
            models.UniqueConstraint(
                fields=["room_type", "date"],
                name="unique_room_type_availability_per_date",
            )
        ]
        indexes = [
            models.Index(fields=["room_type", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.room_type.code} @ {self.date}: {self.allotment - self.booked} free"

    @property
    def available_allotment(self):
        if self.stop_sell or self.closed:
            return 0
        return max(0, self.allotment - self.booked)

    @property
    def available_units(self):
        """Alias used by booking engine / catalog serializers."""
        return self.available_allotment


class RatePlanPrice(models.Model):
    """Nightly price for a rate plan × room type × date."""

    rate_plan = models.ForeignKey(
        RatePlan,
        on_delete=models.CASCADE,
        related_name="prices",
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rate_prices",
    )
    date = models.DateField()
    price_1 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_2 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_3 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_4 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    price_by_occupancy = models.JSONField(
        default=dict,
        blank=True,
        help_text='Optional map of occupancy → price, e.g. {"1": 80, "2": 100}',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rate_plan", "room_type", "date"]
        constraints = [
            models.UniqueConstraint(
                fields=["rate_plan", "room_type", "date"],
                name="unique_rate_plan_price_per_date",
            )
        ]
        indexes = [
            models.Index(fields=["rate_plan", "room_type", "date"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.rate_plan.code}/{self.room_type.code} @ {self.date}"
