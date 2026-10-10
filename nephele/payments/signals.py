"""
Payment signals for automatic payment creation from bookings

When a booking is confirmed, automatically create a payment record.
This eliminates the need for staff to manually create payments.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from room.models import Booking
from .models import Payment, PaymentMethod, Invoice


@receiver(post_save, sender=Booking)
def auto_create_payment_on_booking_confirmation(sender, instance, created, update_fields, **kwargs):
    """
    Automatically create a Payment when a Booking is confirmed.
    
    This signal:
    1. Listens for Booking model saves
    2. Checks if status is 'confirmed'
    3. Calculates total cost from dates and pricing
    4. Creates Payment object if it doesn't exist
    5. Logs the payment creation
    
    Args:
        sender: Booking model
        instance: Booking instance being saved
        created: Boolean if this is a new Booking
        update_fields: Set of fields that were updated
    """
    
    # Only process if status is confirmed
    if instance.status != 'confirmed':
        return
    
    # Check if payment already exists for this booking
    if Payment.objects.filter(booking=instance).exists():
        print(f"[PAYMENT] Payment already exists for booking {instance.id}")
        return
    
    try:
        # Get default payment method (Credit Card)
        payment_method = PaymentMethod.objects.filter(
            name='Credit Card',
            is_active=True
        ).first()
        
        if not payment_method:
            # Fallback to first active payment method
            payment_method = PaymentMethod.objects.filter(is_active=True).first()
        
        if not payment_method:
            print(f"[PAYMENT ERROR] No active payment method found for booking {instance.id}")
            return
        
        # Calculate stay duration and total cost
        num_days = (instance.check_out_date - instance.check_in_date).days
        
        if num_days <= 0:
            print(f"[PAYMENT ERROR] Invalid dates for booking {instance.id}")
            return
        
        # Use actual_price if set, otherwise use base_price
        price_per_night = instance.actual_price or instance.base_price
        total_amount = Decimal(str(num_days)) * price_per_night
        
        # Create payment record
        payment = Payment.objects.create(
            guest=instance.guest,
            booking=instance,
            payment_method=payment_method,
            amount=total_amount,
            currency='EUR',
            status='pending',
            description=f"Payment for {num_days}-night booking in room {instance.room.room_number}",
            notes=f"Auto-created on booking confirmation. Check-in: {instance.check_in_date}, Check-out: {instance.check_out_date}"
        )
        
        print(f"[PAYMENT] ✓ Created payment {payment.reference_code} for booking {instance.id}")
        print(f"  - Amount: €{total_amount}")
        print(f"  - Guest: {instance.guest}")
        print(f"  - Room: {instance.room.room_number}")
        print(f"  - Duration: {num_days} nights")
        
    except Exception as e:
        print(f"[PAYMENT ERROR] Failed to create payment for booking {instance.id}: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Booking)
def auto_create_invoice_on_payment_completion(sender, instance, update_fields, **kwargs):
    """
    Automatically create an Invoice when Payment is completed.
    
    Note: This actually watches bookings for payment completion indirect signal.
    For direct payment monitoring, a signal on Payment model would be better.
    This is a helper that can be extended.
    
    Args:
        sender: Booking model
        instance: Booking instance
        update_fields: Fields that were updated
    """
    
    # Check if booking is checked out (payment should be complete)
    if instance.status != 'checked_out':
        return
    
    try:
        # Get associated payment
        payment = Payment.objects.filter(booking=instance).first()
        
        if not payment:
            return
        
        # Check if invoice already exists
        if hasattr(payment, 'invoice') and payment.invoice:
            return
        
        # Only create invoice if payment is completed
        if payment.status != 'completed':
            return
        
        # Prefer booking tax fields; fall back to 24% VAT on payment amount
        from payments.invoice_lines import ensure_invoice_lines

        vat_amount = instance.vat_amount
        if vat_amount is None:
            vat_amount = payment.amount * Decimal("0.24")
        total_with_vat = (
            instance.actual_price
            if instance.actual_price is not None
            else payment.amount + vat_amount
        )

        invoice = Invoice(
            guest=instance.guest,
            payment=payment,
            booking=instance,
            amount=payment.amount,
            tax_amount=vat_amount,
            total_amount=total_with_vat,
            status="issued",
            description="",
            notes="Auto-created from completed payment on checkout",
        )
        ensure_invoice_lines(invoice, instance, force=True)
        invoice.save()

        print(f"[INVOICE] ✓ Created invoice {invoice.invoice_number} for booking {instance.id}")
        
    except Exception as e:
        print(f"[INVOICE ERROR] Failed to create invoice for booking {instance.id}: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Invoice)
def apply_lines_on_invoice_save(sender, instance, created, **kwargs):
    """Cover manual InvoiceForm / admin / API creates that skip checkout signal."""
    if not instance.booking_id:
        return
    if instance.line_items and not created:
        return
    try:
        from payments.invoice_lines import ensure_invoice_lines

        before = list(instance.line_items or [])
        ensure_invoice_lines(instance, force=created and not before)
        after = list(instance.line_items or [])
        if after != before:
            Invoice.objects.filter(pk=instance.pk).update(
                description=instance.description,
                notes=instance.notes,
                line_items=instance.line_items,
            )
    except Exception:
        pass
