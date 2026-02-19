"""
Serializers for accounts app models

Per Task 4: API Design Specifications
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Guest, Employee, Task, Role


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class GuestSerializer(serializers.ModelSerializer):
    """Serializer for Guest model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Guest
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'email', 'first_name', 'last_name', 'phone_number',
            'address', 'city', 'country', 'postal_code',
            'preferences', 'number_of_bookings', 'total_nights_stayed',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'number_of_bookings', 'total_nights_stayed',
            'created_at', 'updated_at'
        ]
    
    def get_user_full_name(self, obj) -> str:
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return f"{obj.first_name} {obj.last_name}"


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model"""
    
    user_detail = serializers.SerializerMethodField()
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'user_detail', 'phone_number',
            'salary', 'position', 'department', 'hire_date',
            'status', 'property', 'property_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_detail(self, obj) -> dict | None:
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
            }
        return None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    
    employee_name = serializers.CharField(source='employee', read_only=True)
    booking_reference = serializers.CharField(source='booking.id', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'employee', 'employee_name', 'title', 'description',
            'start_time', 'end_time', 'status', 'priority',
            'booking', 'booking_reference', 'property', 'property_name',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = User.objects.create(**validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
