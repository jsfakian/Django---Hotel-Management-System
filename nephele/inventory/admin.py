from django.contrib import admin

from .models import (
    AvailabilitySyncLog,
    RatePlan,
    RatePlanPrice,
    RoomAvailability,
    RoomType,
    RoomTypeAvailability,
    RoomTypeAvailabilityAudit,
)


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "date",
        "total_units",
        "available_units",
        "booked_units",
        "blocked_units",
        "is_available",
        "occupancy_rate",
    )
    list_filter = ("date", "room__property", "staff_override", "created_at")
    search_fields = ("room__room_number", "room__property__name")
    readonly_fields = ("is_available", "occupancy_rate", "created_at", "updated_at")
    date_hierarchy = "date"


@admin.register(AvailabilitySyncLog)
class AvailabilitySyncLogAdmin(admin.ModelAdmin):
    list_display = (
        "channel",
        "sync_type",
        "sync_status",
        "rooms_affected",
        "attempt_count",
        "completed_at",
    )
    list_filter = ("channel", "sync_status", "sync_type", "created_at")
    search_fields = ("channel__channel_name", "property__name")
    readonly_fields = ("created_at", "completed_at", "response_data")
    date_hierarchy = "created_at"


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "property", "max_occupancy", "base_price", "is_active")
    list_filter = ("property", "is_active")
    search_fields = ("code", "name")


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "property", "meal_plan", "is_refundable", "is_active")
    list_filter = ("property", "meal_plan", "is_refundable", "is_active")
    search_fields = ("code", "name")
    filter_horizontal = ("room_types",)


@admin.register(RoomTypeAvailability)
class RoomTypeAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "room_type",
        "date",
        "allotment",
        "booked",
        "stop_sell",
        "min_stay",
        "cta",
        "ctd",
    )
    list_filter = ("stop_sell", "closed", "room_type__property")
    date_hierarchy = "date"


@admin.register(RatePlanPrice)
class RatePlanPriceAdmin(admin.ModelAdmin):
    list_display = ("rate_plan", "room_type", "date", "price_1", "price_2")
    list_filter = ("rate_plan__property",)
    date_hierarchy = "date"


@admin.register(RoomTypeAvailabilityAudit)
class RoomTypeAvailabilityAuditAdmin(admin.ModelAdmin):
    """Immutable audit log — view-only in Django admin."""

    list_display = (
        "room_type",
        "date",
        "old_allotment",
        "new_allotment",
        "old_staff_override",
        "new_staff_override",
        "changed_by",
        "changed_at",
    )
    list_filter = ("room_type__property", "changed_at")
    search_fields = ("note", "room_type__code")
    readonly_fields = (
        "room_type",
        "date",
        "old_allotment",
        "new_allotment",
        "old_staff_override",
        "new_staff_override",
        "changed_by",
        "changed_at",
        "note",
    )
    date_hierarchy = "changed_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
