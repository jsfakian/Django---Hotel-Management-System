from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods

from .models import Property, PropertyAmenity, PropertyPolicy, TravelAgency
from .forms import PropertyForm, PropertyAmenityForm, PropertyPolicyForm


def get_user_role(user):
    """Get the role of the current user"""
    try:
        return str(user.groups.all()[0])
    except:
        return None


@login_required(login_url='login')
@require_http_methods(["GET"])
def properties_list(request):
    """List all properties with role-based filtering"""
    role = get_user_role(request.user)
    
    if role == 'admin':
        properties = Property.objects.all()
    elif role == 'manager':
        properties = Property.objects.filter(manager=request.user)
    else:
        # Guests and staff can only view active properties
        properties = Property.objects.filter(is_active=True)
    
    # Filter by search term
    search = request.GET.get('search', '')
    if search:
        properties = properties.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Filter by city
    city = request.GET.get('city', '')
    if city:
        properties = properties.filter(city=city)
    
    context = {
        'role': role,
        'properties': properties,
        'search': search,
        'cities': Property.objects.values_list('city', flat=True).distinct()
    }
    
    return render(request, 'common_pages/properties-list.html', context)


@login_required(login_url='login')
def property_detail(request, pk):
    """View property details"""
    property_obj = get_object_or_404(Property, pk=pk)
    role = get_user_role(request.user)
    
    # Check permissions
    if role == 'admin' or (role == 'manager' and property_obj.manager == request.user):
        can_edit = True
    else:
        can_edit = False
    
    # Get related data
    amenities = property_obj.amenities.all()
    policy = PropertyPolicy.objects.filter(property=property_obj).first()
    
    # Get room statistics
    from room.models import Room, Booking
    from datetime import date
    today = date.today()
    
    total_rooms = Room.objects.filter(property=property_obj).count()
    booked_today = Booking.objects.filter(
        roomNumber__property=property_obj,
        startDate__lte=today,
        endDate__gt=today
    ).count()
    
    context = {
        'role': role,
        'property': property_obj,
        'can_edit': can_edit,
        'amenities': amenities,
        'policy': policy,
        'total_rooms': total_rooms,
        'booked_rooms': booked_today,
        'available_rooms': total_rooms - booked_today,
    }
    
    return render(request, 'common_pages/property-detail.html', context)


@login_required(login_url='login')
def property_create(request):
    """Create a new property (Admin and Manager only)"""
    role = get_user_role(request.user)
    
    # Check permissions
    if role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to create properties.')
        return redirect('properties-list')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            
            # Set manager if not admin
            if role == 'manager':
                property_obj.manager = request.user
            
            property_obj.save()
            
            # Create default policy
            PropertyPolicy.objects.get_or_create(
                property=property_obj,
                defaults={
                    'cancellation_policy': 'Standard cancellation policy',
                    'pet_policy': 'Pets not allowed',
                    'smoking_policy': 'Non-smoking property',
                    'children_policy': 'Children welcome',
                }
            )
            
            messages.success(request, f'Property "{property_obj.name}" created successfully.')
            return redirect('property-detail', pk=property_obj.pk)
    else:
        form = PropertyForm()
    
    context = {
        'role': role,
        'form': form,
        'title': 'Create Property'
    }
    
    return render(request, 'common_pages/property-form.html', context)


@login_required(login_url='login')
def property_edit(request, pk):
    """Edit a property (Admin and Manager only)"""
    property_obj = get_object_or_404(Property, pk=pk)
    role = get_user_role(request.user)
    
    # Check permissions
    if role == 'admin' or (role == 'manager' and property_obj.manager == request.user):
        pass
    else:
        messages.error(request, 'You do not have permission to edit this property.')
        return redirect('property-detail', pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Property "{property_obj.name}" updated successfully.')
            return redirect('property-detail', pk=property_obj.pk)
    else:
        form = PropertyForm(instance=property_obj)
    
    context = {
        'role': role,
        'form': form,
        'property': property_obj,
        'title': f'Edit {property_obj.name}'
    }
    
    return render(request, 'common_pages/property-form.html', context)


@login_required(login_url='login')
def property_delete(request, pk):
    """Delete a property (Admin only)"""
    property_obj = get_object_or_404(Property, pk=pk)
    role = get_user_role(request.user)
    
    # Check permissions
    if role != 'admin':
        messages.error(request, 'Only admins can delete properties.')
        return redirect('property-detail', pk=pk)
    
    if request.method == 'POST':
        property_name = property_obj.name
        property_obj.delete()
        messages.success(request, f'Property "{property_name}" deleted successfully.')
        return redirect('properties-list')
    
    context = {
        'role': role,
        'property': property_obj,
    }
    
    return render(request, 'common_pages/property-confirm-delete.html', context)


@login_required(login_url='login')
def property_amenities(request, pk):
    """Manage amenities for a property"""
    property_obj = get_object_or_404(Property, pk=pk)
    role = get_user_role(request.user)
    
    # Check permissions
    if role == 'admin' or (role == 'manager' and property_obj.manager == request.user):
        pass
    else:
        messages.error(request, 'You do not have permission to manage this property.')
        return redirect('property-detail', pk=pk)
    
    amenities = property_obj.amenities.all()
    
    if request.method == 'POST':
        form = PropertyAmenityForm(request.POST)
        if form.is_valid():
            amenity = form.save(commit=False)
            amenity.property = property_obj
            amenity.save()
            messages.success(request, 'Amenity added successfully.')
            return redirect('property-amenities', pk=pk)
    else:
        form = PropertyAmenityForm(initial={'property': property_obj})
    
    context = {
        'role': role,
        'property': property_obj,
        'amenities': amenities,
        'form': form,
    }
    
    return render(request, 'common_pages/property-amenities.html', context)


@login_required(login_url='login')
def property_policy(request, pk):
    """Manage policies for a property"""
    property_obj = get_object_or_404(Property, pk=pk)
    role = get_user_role(request.user)
    
    # Check permissions
    if role == 'admin' or (role == 'manager' and property_obj.manager == request.user):
        pass
    else:
        messages.error(request, 'You do not have permission to manage this property.')
        return redirect('property-detail', pk=pk)
    
    policy, created = PropertyPolicy.objects.get_or_create(property=property_obj)
    
    if request.method == 'POST':
        form = PropertyPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Policy updated successfully.')
            return redirect('property-policy', pk=pk)
    else:
        form = PropertyPolicyForm(instance=policy)
    
    context = {
        'role': role,
        'property': property_obj,
        'policy': policy,
        'form': form,
    }
    
    return render(request, 'common_pages/property-policy.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def travel_agency_list(request):
    """HTML list view for all travel agencies."""
    role = get_user_role(request.user)
    agencies = TravelAgency.objects.all().order_by('name')
    return render(request, 'common_pages/travel-agencies.html', {
        'role': role,
        'agencies': agencies,
    })
