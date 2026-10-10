# nephele/room/models.py
"""
Room, Booking, and related models
"""

from django.db import models
from django.utils import timezone

from accounts.models import Guest


class Room(models.Model):
    """Physical room in a property."""

    ROOM_TYPE_CHOICES = (
        ("single", "Single Room"),
        ("double", "Double Room"),
        ("suite", "Suite"),
        ("deluxe", "Deluxe"),
        ("luxury", "Luxury"),
        ("economic", "Economic"),
    )

    STATUS_CHOICES = (
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("maintenance", "Maintenance"),
        ("cleaning", "Cleaning"),
        ("reserved", "Reserved"),
    )

    room_number = models.CharField(max_length=50)
    floor = models.IntegerField()
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    room_type_fk = models.ForeignKey(
        "inventory.RoomType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rooms",
        help_text="Catalog room type (WebHotelier parity)",
    )

    capacity = models.PositiveIntegerField()
    number_of_beds = models.PositiveIntegerField()

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
    )
    status_start_date = models.DateField(null=True, blank=True)
    status_end_date = models.DateField(null=True, blank=True)

    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON array of room amenities",
    )

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.CASCADE,
        related_name="rooms",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["property", "room_number"]
        indexes = [
            models.Index(fields=["property", "status"]),
            models.Index(fields=["room_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "room_number"],
                name="unique_room_number_per_property",
            )
        ]

    def __str__(self):
        return f"Room {self.room_number} - {self.property.name}"


class Booking(models.Model):
    """Reservation / booking record."""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("cancelled", "Cancelled"),
        ("no_show", "No-Show"),
        ("held", "Held"),
    )

    BOOKING_SOURCE_CHOICES = (
        ("direct_website", "Direct Website"),
        ("booking_com", "Booking.com"),
        ("trivago", "Trivago"),
        ("phone", "Phone Call"),
        ("travel_agency", "Travel Agency"),
        ("airbnb", "Airbnb"),
        ("expedia", "Expedia"),
        ("booking_engine", "Booking Engine"),
        ("ical", "iCal"),
        ("other", "Other"),
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True,
    )
    room_type = models.ForeignKey(
        "inventory.RoomType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    rate_plan = models.ForeignKey(
        "inventory.RatePlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    guest = models.ForeignKey(
        Guest,
        on_delete=models.CASCADE,
        null=True,
        related_name="bookings",
    )

    check_in_date = models.DateField()
    check_out_date = models.DateField()
    date_of_reservation = models.DateField(default=timezone.localdate)

    number_of_guests = models.PositiveIntegerField(default=1)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    children_ages = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    hold_token = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="Opaque token required for public hold confirm/cancel/modify",
    )

    related_bookings = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_members",
        help_text="Parent booking for group / multi-room reservations",
    )

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    actual_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    vat_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    climate_resilience_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    guest_registration_id = models.CharField(max_length=100, blank=True)
    # ΣΑΕ / police sheet fields (export first; ministry API later)
    guest_document_type = models.CharField(max_length=32, blank=True)
    guest_document_number = models.CharField(max_length=64, blank=True)
    guest_nationality = models.CharField(max_length=64, blank=True)
    guest_birth_date = models.DateField(null=True, blank=True)
    police_sheet_exported_at = models.DateTimeField(null=True, blank=True)
    # ΣΗΜΑ stay linkage (ministry registry)
    shima_stay_purpose = models.CharField(max_length=64, blank=True)
    mhte_registry_number = models.CharField(max_length=64, blank=True)

    travel_agency = models.ForeignKey(
        "properties.TravelAgency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    booking_source = models.CharField(
        max_length=30,
        choices=BOOKING_SOURCE_CHOICES,
        default="direct_website",
        help_text="Source of the booking (used only if no travel agency selected)",
    )

    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-check_in_date"]
        indexes = [
            models.Index(fields=["room", "check_in_date", "check_out_date"]),
            models.Index(fields=["guest", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        room_label = self.room.room_number if self.room_id else "unassigned"
        return f"Booking {self.id} - {room_label} ({self.check_in_date})"

    def num_of_dep(self):
        """Legacy method"""
        return self.guests_list.count()


class Dependees(models.Model):
    """Guest dependents/companions for a booking."""

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="guests_list",
    )
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Dependees"

    def __str__(self):
        return f"{self.name} ({self.booking.id})"


class Refund(models.Model):
    """Refund requests for bookings."""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("processed", "Processed"),
    )

    guest = models.ForeignKey(
        Guest,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund {self.id} - {self.guest}"


class RoomService(models.Model):
    """Room services and amenities provided to guests."""

    SERVICE_TYPE_CHOICES = (
        ("food", "Food Service"),
        ("cleaning", "Cleaning Service"),
        ("technical", "Technical Service"),
        ("maintenance", "Maintenance"),
        ("concierge", "Concierge"),
        ("laundry", "Laundry"),
        ("other", "Other"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="room_services",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="services",
    )
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["room", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.room.room_number}"
