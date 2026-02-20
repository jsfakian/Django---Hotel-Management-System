from django.contrib import admin
from .models import RoomAvailability, AvailabilitySyncLog


@admin.register(RoomAvailability)
class RoomAvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for centralized room availability (Nephele)"""
    
    list_display = (
        'room', 'date', 'total_units', 'available_units',
        'booked_units', 'blocked_units', 'is_available', 'occupancy_rate'
    )
    list_filter = ('date', 'room__property', 'staff_override', 'created_at')
    search_fields = ('room__room_number', 'room__property__name')
    readonly_fields = (
        'is_available', 'occupancy_rate', 'created_at', 'updated_at'
    )
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Room & Date', {
            'fields': ('room', 'date')
        }),
        ('Availability Units', {
            'fields': (
                'total_units', 'available_units', 'booked_units',
                'blocked_units', 'overbooked_units'
            )
        }),
        ('Pricing', {
            'fields': ('base_price', 'dynamic_price')
        }),
        ('Staff Override', {
            'fields': ('staff_override', 'updated_by', 'notes')
        }),
        ('Status', {
            'fields': ('is_available', 'occupancy_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AvailabilitySyncLog)
class AvailabilitySyncLogAdmin(admin.ModelAdmin):
    """Admin interface for tracking availability synchronization to channels"""
    
    list_display = (
        'channel', 'sync_type', 'sync_status', 'rooms_affected',
        'attempt_count', 'completed_at'
    )
    list_filter = ('channel', 'sync_status', 'sync_type', 'created_at')
    search_fields = ('channel__channel_name', 'property__name')
    readonly_fields = (
        'created_at', 'completed_at', 'response_data'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Sync Details', {
            'fields': ('property', 'channel', 'sync_type', 'sync_status')
        }),
        ('Scope', {
            'fields': ('rooms_affected', 'date_from', 'date_to')
        }),
        ('Execution', {
            'fields': ('attempt_count', 'created_at', 'completed_at', 'next_retry_at')
        }),
        ('Response', {
            'fields': ('response_code', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
