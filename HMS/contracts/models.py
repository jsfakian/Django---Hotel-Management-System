from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class Contract(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", _("Pending")
        APPROVED = "Approved", _("Approved")
        REJECTED = "Rejected", _("Rejected")

    class ContractType(models.TextChoices):
        GUARANTEE = "Guarantee", _("Guarantee")
        ALLOTMENT = "Allotment", _("Allotment")

    hotel_manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contracts_created")
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contracts_signed")
    
    contract_type = models.CharField(max_length=20, choices=ContractType.choices, default=ContractType.ALLOTMENT)
    
    allocation_percentage = models.FloatField(blank=True, null=True, help_text="Percentage of rooms allocated (for Allotment contracts)")
    allocated_rooms = models.IntegerField(blank=True, null=True, help_text="Fixed number of rooms (for Guarantee contracts)")
    
    commission_rate = models.FloatField(help_text="Percentage commission for the agent")
    payment_terms = models.TextField(help_text="Describe payment frequency, deposit requirements, etc.")
    cancellation_policy = models.TextField(help_text="Describe cancellation terms and penalties.")
    
    start_date = models.DateField(help_text="Start date of the contract")
    end_date = models.DateField(help_text="End date of the contract")

    contract_text = models.TextField()
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    hotel_manager_signature = models.CharField(max_length=255, blank=True, null=True)
    agent_signature = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.contract_type} Contract {self.id} - {self.hotel_manager.username} & {self.agent.username}"
