from django.contrib import admin
from .models import Channel, ChannelBooking


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """Admin interface for OTA channel configurations"""
    
    list_display = (
        'channel_name', 'property', 'is_active', 'sync_enabled',
        'accept_bookings', 'error_count', 'last_sync_at'
    )
    list_filter = ('channel_name', 'is_active', 'sync_enabled', 'created_at')
    search_fields = ('property__name', 'account_id', 'channel_name')
    readonly_fields = (
        'created_at', 'updated_at', 'last_sync_at', 'last_error'
    )
    
    fieldsets = (
        ('Channel Information', {
            'fields': ('property', 'channel_name', 'channel_type')
        }),
        ('API Credentials', {
            'fields': ('account_id', 'api_key', 'api_secret'),
            'classes': ('collapse',)
        }),
        ('Synchronization Settings', {
            'fields': ('is_active', 'sync_enabled', 'accept_bookings')
        }),
        ('Room & Rate Mappings', {
            'fields': ('mapping_config',),
            'classes': ('collapse',)
        }),
        ('Sync Status', {
            'fields': (
                'last_sync_at', 'last_error', 'error_count'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make api_key readonly in change view"""
        if obj:  # Editing existing object
            return self.readonly_fields + ('api_key',)
        return self.readonly_fields


@admin.register(ChannelBooking)
class ChannelBookingAdmin(admin.ModelAdmin):
    """Admin interface for tracking channel booking references"""
    
    list_display = ('channel_booking_id', 'channel', 'nephele_booking', 'sync_status', 'created_at')
    list_filter = ('channel', 'sync_status', 'created_at')
    search_fields = ('channel_booking_id', 'nephele_booking__id')
    readonly_fields = ('created_at', 'updated_at', 'channel_data')
    
    fieldsets = (
        ('Booking References', {
            'fields': ('channel', 'channel_booking_id', 'nephele_booking')
        }),
        ('Sync Status', {
            'fields': ('sync_status',)
        }),
        ('Channel Data', {
            'fields': ('channel_data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
