from django import forms
from django.contrib.auth.models import User
from .models import Property, PropertyAmenity, PropertyPolicy


class PropertyForm(forms.ModelForm):
    """Form for creating and editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'name', 'location', 'address', 'city', 'postal_code', 'country',
            'phone_number', 'email', 'website', 'total_rooms', 'star_rating', 'manager'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Property Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hotel@example.com'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'total_rooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'star_rating': forms.Select(attrs={'class': 'form-control'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }


class PropertyAmenityForm(forms.ModelForm):
    """Form for managing property amenities"""
    
    class Meta:
        model = PropertyAmenity
        fields = ['property', 'amenity_type', 'description']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'amenity_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }


class PropertyPolicyForm(forms.ModelForm):
    """Form for managing property policies"""
    
    class Meta:
        model = PropertyPolicy
        fields = [
            'property', 'check_in_time', 'check_out_time',
            'cancellation_policy', 'pet_policy', 'smoking_policy', 'children_policy'
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'check_in_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'cancellation_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Cancellation Policy'}),
            'pet_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Pet Policy'}),
            'smoking_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Smoking Policy'}),
            'children_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Children Policy'}),
        }
