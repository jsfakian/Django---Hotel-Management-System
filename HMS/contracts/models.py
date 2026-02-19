"""
Contract management models

Per deliverables:
- DELIVERABLES-Task4-SystemArchitecture.md
- tasks/phase-2-development/task-5a-backend-core.md
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Contract(models.Model):
    """
    Contract model for managing agreements between properties and travel agencies.
    Per Task 4: Contract entity
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('signed_property', 'Signed by Property'),
        ('signed_agency', 'Signed by Agency'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('rejected', 'Rejected'),
    )
    
    CONTRACT_TYPE_CHOICES = (
        ('guarantee', 'Guarantee Contract'),
        ('allotment', 'Allotment Contract'),
        ('commission', 'Commission Agreement'),
        ('exclusive', 'Exclusive Agreement'),
    )
    
    # Parties
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    travel_agency = models.ForeignKey(
        'properties.TravelAgency',
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    property_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contracts_created',
        limit_choices_to={'groups__name': 'hotel_manager'}
    )
    
    # Contract details
    contract_type = models.CharField(
        max_length=50,
        choices=CONTRACT_TYPE_CHOICES,
        default='allotment'
    )
    
    # Allocation (for Allotment contracts)
    allocation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of rooms allocated (for Allotment contracts)"
    )
    allocated_rooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Fixed number of rooms (for Guarantee contracts)"
    )
    
    # Commission and payments
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Commission percentage for the travel agency"
    )
    payment_terms = models.TextField(
        help_text="Describe payment frequency, deposit requirements, etc."
    )
    
    # Cancellation and terms
    cancellation_policy = models.TextField(
        help_text="Describe cancellation terms and penalties."
    )
    special_terms = models.TextField(
        blank=True,
        help_text="Additional special terms or conditions"
    )
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Document
    contract_text = models.TextField()
    document_file = models.FileField(
        upload_to='contracts/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Status and signatures
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft'
    )
    property_manager_signed_at = models.DateTimeField(null=True, blank=True)
    property_manager_signature = models.CharField(max_length=255, blank=True)
    
    travel_agency_signed_at = models.DateTimeField(null=True, blank=True)
    travel_agency_signature = models.CharField(max_length=255, blank=True)
    
    # Management
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [('property', 'travel_agency')]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.get_contract_type_display()} - {self.property.name} & {self.travel_agency.name}"
    
    def is_active(self):
        """Check if contract is currently active"""
        now = timezone.now().date()
        return (self.status == 'active' and 
                self.start_date <= now <= self.end_date)
    
    def is_expired(self):
        """Check if contract has expired"""
        now = timezone.now().date()
        return now > self.end_date
    
    def sign_property(self, signature='', user=None):
        """Record property manager signature"""
        self.property_manager_signature = signature
        self.property_manager_signed_at = timezone.now()
        if self.status == 'draft':
            self.status = 'pending'
        elif self.status == 'signed_agency':
            self.status = 'active'
        else:
            self.status = 'signed_property'
        self.save()
    
    def sign_agency(self, signature=''):
        """Record travel agency signature"""
        self.travel_agency_signature = signature
        self.travel_agency_signed_at = timezone.now()
        if self.status == 'signed_property':
            self.status = 'active'
        else:
            self.status = 'signed_agency'
        self.save()

