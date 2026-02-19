from django.contrib import admin
from .models import Property, PropertyAmenity, PropertyPolicy


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'city', 'total_rooms', 'star_rating', 'is_active']
    list_filter = ['is_active', 'star_rating', 'city', 'country']
    search_fields = ['name', 'location', 'city', 'country']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'address', 'city', 'postal_code', 'country')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'website')
        }),
        ('Property Details', {
            'fields': ('total_rooms', 'star_rating', 'manager', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    list_display = ['property', 'amenity_type']
    list_filter = ['property', 'amenity_type']
    search_fields = ['property__name', 'amenity_type']


@admin.register(PropertyPolicy)
class PropertyPolicyAdmin(admin.ModelAdmin):
    list_display = ['property', 'check_in_time', 'check_out_time']
    search_fields = ['property__name']
    readonly_fields = ['created_at', 'updated_at']
