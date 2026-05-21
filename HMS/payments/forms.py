from django import forms
from .models import Payment, Invoice, RefundRequest


class PaymentForm(forms.ModelForm):
    """Form for processing payments"""
    
    card_number = forms.CharField(
        max_length=19,
        min_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'pattern': '[0-9 ]*',
            'autocomplete': 'cc-number',
            'aria-label': 'Card number',
            'aria-describedby': 'card-number-error',
            'aria-required': 'false',
        })
    )

    card_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cardholder Name',
            'autocomplete': 'cc-name',
            'aria-label': 'Name on card',
            'aria-describedby': 'card-name-error',
            'aria-required': 'false',
        })
    )

    expiry_date = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/YY',
            'pattern': '[0-9/]*',
            'autocomplete': 'cc-exp',
            'aria-label': 'Card expiry date (MM/YY)',
            'aria-describedby': 'expiry-error',
            'aria-required': 'false',
        })
    )

    cvc = forms.CharField(
        max_length=4,
        min_length=3,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'CVC',
            'autocomplete': 'cc-csc',
            'aria-label': 'Card security code (CVC)',
            'aria-describedby': 'cvc-error',
            'aria-required': 'false',
        })
    )

    class Meta:
        model = Payment
        fields = ['payment_method', 'amount']
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'aria-label': 'Payment method',
                'aria-required': 'true',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'step': '0.01',
                'aria-label': 'Payment amount',
                'aria-readonly': 'true',
            }),
        }


class PaymentVerificationForm(forms.Form):
    """Form for verifying payment with code"""
    
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autofocus': True,
            'aria-label': 'Six-digit verification code',
            'aria-describedby': 'verification-hint verification-error',
            'aria-required': 'true',
        }),
        label='Enter the 6-digit verification code sent to your email'
    )


class RefundRequestForm(forms.ModelForm):
    """Form for requesting refunds"""
    
    class Meta:
        model = RefundRequest
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please explain the reason for your refund request...'
            }),
        }


class InvoiceFilterForm(forms.Form):
    """Form for filtering invoices"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + list(Invoice.STATUS_CHOICES)
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class InvoiceForm(forms.ModelForm):
    """Form for creating and editing invoices"""
    
    transmit_to_mydata = forms.BooleanField(
        required=False,
        initial=False,
        label='Transmit to MyData (AADE)',
        help_text='If checked, the invoice will be automatically transmitted to the Greek tax authority after creation',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    class Meta:
        model = Invoice
        fields = ['guest', 'payment', 'booking', 'amount', 'tax_amount', 'total_amount', 'status', 'description', 'due_date', 'notes']
        widgets = {
            'guest': forms.Select(attrs={'class': 'form-control'}),
            'payment': forms.Select(attrs={'class': 'form-control'}),
            'booking': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Invoice description (e.g., Room accommodation, Services, etc.)'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }
