from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from datetime import datetime, timedelta

from accounts.models import Guest
from room.models import Booking, Room, RoomService


class PaymentMethod(models.Model):
    """
    Payment methods supported by the system (Credit Card, Debit Card, etc.)
    """
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('wallet', 'Digital Wallet'),
        ('mobile', 'Mobile Payment'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    requires_verification = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_payment_type_display()})"


class Payment(models.Model):
    """
    Payment records for bookings and services.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='payments')
    booking = models.ForeignKey(
        Booking, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payments'
    )
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Transaction information
    transaction_id = models.CharField(max_length=100, unique=True)
    reference_code = models.CharField(max_length=50, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional info
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Verification
    verification_code = models.CharField(max_length=6, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verification_verified_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.reference_code} - {self.amount} {self.currency}"
    
    def mark_as_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save()
        
        # Generate invoice
        self.generate_invoice()
    
    def mark_as_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        self.notes = reason
        self.save()
    
    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        import random
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.verification_code = code
        self.verification_sent_at = timezone.now()
        self.save()
        return code
    
    def verify(self, code):
        """Verify payment with code"""
        if self.verification_code == code and not self.is_verified:
            self.is_verified = True
            self.verification_verified_at = timezone.now()
            self.save()
            self.mark_as_completed()
            return True
        return False
    
    def generate_invoice(self):
        """Generate invoice for this payment"""
        Invoice.objects.get_or_create(
            payment=self,
            defaults={
                'guest': self.guest,
                'amount': self.amount,
                'description': f'Payment for {self.description}',
            }
        )
    
    def is_expired(self):
        """Check if payment is expired (24 hours)"""
        if self.status in ['completed', 'refunded']:
            return False
        
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time


class Invoice(models.Model):
    """
    Invoices generated from payments
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='invoices')
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice'
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    description = models.TextField()
    
    # Dates
    issued_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['guest', '-issued_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.invoice_number:
            self.generate_invoice_number()
        if not self.due_date:
            self.due_date = (timezone.now() + timedelta(days=30)).date()
        if not self.total_amount:
            self.total_amount = self.amount + self.tax_amount
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        import uuid
        
        date_str = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        self.invoice_number = f"INV-{date_str}-{unique_id}"
    
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status == 'paid':
            return False
        
        return timezone.now().date() > self.due_date
    
    def mark_as_paid(self):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_date = timezone.now().date()
        self.save()


class RefundRequest(models.Model):
    """
    Refund requests for cancellations or disputes
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REASON_CHOICES = [
        ('cancellation', 'Booking Cancellation'),
        ('overcharge', 'Overcharge'),
        ('dispute', 'Payment Dispute'),
        ('damaged', 'Damaged/Defective Item'),
        ('unsatisfactory', 'Unsatisfactory Service'),
        ('other', 'Other Reason'),
    ]
    
    # Relationships
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refund_requests')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='refund_requests')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_refunds',
        limit_choices_to={'groups__name__in': ['admin', 'manager']}
    )
    
    # Refund details
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    requested_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Rejection info
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['guest', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Refund Request {self.id} - {self.status}"
    
    def approve(self, user=None):
        """Approve refund request"""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.processed_by = user
        self.save()
    
    def reject(self, reason, user=None):
        """Reject refund request"""
        self.status = 'rejected'
        self.rejection_reason = reason
        self.processed_by = user
        self.save()
    
    def process(self, user=None):
        """Process approved refund"""
        if self.status != 'approved':
            raise ValueError('Only approved refunds can be processed')
        
        self.status = 'processed'
        self.processed_at = timezone.now()
        self.processed_by = user
        
        # Update payment status
        self.payment.status = 'refunded'
        self.payment.save()
        
        self.save()


class PaymentTransaction(models.Model):
    """
    Detailed transaction log for payment processing
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('fee', 'Fee'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"
