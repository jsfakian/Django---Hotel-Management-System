from django.contrib import admin
from .models import Payment, PaymentMethod, Invoice, RefundRequest, PaymentTransaction


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'is_active', 'requires_verification']
    list_filter = ['payment_type', 'is_active']
    search_fields = ['name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference_code', 'guest', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['reference_code', 'transaction_id', 'guest__user__username']
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'verification_sent_at', 'verification_verified_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('reference_code', 'transaction_id', 'amount', 'currency', 'status')
        }),
        ('Guest & Booking', {
            'fields': ('guest', 'booking', 'payment_method')
        }),
        ('Verification', {
            'fields': ('verification_code', 'is_verified', 'verification_sent_at', 'verification_verified_at')
        }),
        ('Details', {
            'fields': ('description', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at', 'updated_at')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'guest', 'amount', 'status', 'due_date', 'issued_date', 'mydata_transmitted']
    list_filter = ['status', 'issued_date', 'due_date', 'mydata_transmitted']
    search_fields = ['invoice_number', 'guest__user__username']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'mydata_transmission_date', 'mydata_qr_code']
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'status')
        }),
        ('Guest & Booking', {
            'fields': ('guest', 'booking', 'payment')
        }),
        ('Amount Details', {
            'fields': ('amount', 'tax_amount', 'total_amount')
        }),
        ('Dates', {
            'fields': ('issued_date', 'due_date', 'paid_date')
        }),
        ('Description', {
            'fields': ('description', 'notes')
        }),
        ('MyData (AADE) Integration', {
            'fields': ('mydata_transmitted', 'mydata_transmission_id', 'mydata_transmission_date', 'mydata_qr_code', 'mydata_cancel_mark', 'mydata_cancel_date'),
            'classes': ('collapse',),  # Collapsible section
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['transmit_to_mydata']
    
    def transmit_to_mydata(self, request, queryset):
        """Admin action to transmit invoices to MyData"""
        from .mydata_service import get_mydata_service
        
        mydata_service = get_mydata_service()
        transmitted_count = 0
        failed_count = 0
        
        for invoice in queryset:
            if invoice.mydata_transmitted:
                continue
            
            is_valid, errors = mydata_service.validate_invoice_for_transmission(invoice)
            if not is_valid:
                failed_count += 1
                continue
            
            success, _ = mydata_service.transmit_invoice(invoice)
            if success:
                transmitted_count += 1
            else:
                failed_count += 1
        
        self.message_user(request, f'Transmitted {transmitted_count} invoices to MyData. {failed_count} failed.')
    
    transmit_to_mydata.short_description = 'Transmit selected invoices to MyData'


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest', 'refund_amount', 'reason', 'status', 'requested_at']
    list_filter = ['status', 'reason', 'requested_at']
    search_fields = ['guest__user__username', 'payment__reference_code']
    readonly_fields = ['requested_at', 'approved_at', 'processed_at']
    fieldsets = (
        ('Refund Information', {
            'fields': ('payment', 'guest', 'refund_amount')
        }),
        ('Reason', {
            'fields': ('reason', 'description')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Processing', {
            'fields': ('processed_by', 'requested_at', 'approved_at', 'processed_at')
        }),
    )


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['payment', 'transaction_type', 'amount', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['payment__reference_code']
    readonly_fields = ['timestamp']
