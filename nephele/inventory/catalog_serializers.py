from rest_framework import serializers

from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = [
            "id",
            "property",
            "code",
            "name",
            "description",
            "capacity",
            "base_occupancy",
            "max_occupancy",
            "amenities",
            "base_price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RatePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlan
        fields = [
            "id",
            "property",
            "code",
            "name",
            "meal_plan",
            "is_refundable",
            "cancellation_policy",
            "room_types",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomTypeAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomTypeAvailability
        fields = [
            "id",
            "room_type",
            "date",
            "allotment",
            "booked",
            "stop_sell",
            "closed",
            "min_stay",
            "max_stay",
            "cta",
            "ctd",
            "staff_override",
            "updated_by",
            "restrictions",
            "available_units",
        ]
        read_only_fields = ["id", "booked", "available_units", "updated_by"]


class RatePlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlanPrice
        fields = [
            "id",
            "rate_plan",
            "room_type",
            "date",
            "price_1",
            "price_2",
            "price_3",
            "price_4",
            "price_by_occupancy",
        ]


class AvailabilityQuoteSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    children_ages = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    def validate(self, data):
        if data["check_out"] <= data["check_in"]:
            raise serializers.ValidationError("check_out must be after check_in")
        return data


class BulkAvailabilitySerializer(serializers.Serializer):
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    allotment = serializers.IntegerField(required=False, min_value=0)
    stop_sell = serializers.BooleanField(required=False)
    closed = serializers.BooleanField(required=False)
    min_stay = serializers.IntegerField(required=False, min_value=1)
    max_stay = serializers.IntegerField(required=False, min_value=0)
    cta = serializers.BooleanField(required=False)
    ctd = serializers.BooleanField(required=False)
    staff_override = serializers.BooleanField(required=False, default=True)

    def validate(self, data):
        if data["date_to"] <= data["date_from"]:
            raise serializers.ValidationError("date_to must be after date_from")
        return data


class HoldBookingSerializer(serializers.Serializer):
    PAYMENT_MODE_CHOICES = (
        ("deposit", "Deposit"),
        ("pay_at_hotel", "Pay at hotel"),
        ("full", "Pay in full"),
    )

    property_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField()
    rate_plan_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    children_ages = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    guest_email = serializers.EmailField()
    guest_first_name = serializers.CharField(max_length=100)
    guest_last_name = serializers.CharField(max_length=100, required=False, default="")
    guest_phone = serializers.CharField(max_length=40, required=False, default="")
    special_requests = serializers.CharField(required=False, allow_blank=True, default="")
    payment_mode = serializers.ChoiceField(
        choices=PAYMENT_MODE_CHOICES, required=False, default="deposit"
    )
    deposit_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default="30.00", min_value=0
    )


class ConfirmHoldSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    payment_ref = serializers.CharField(required=False, allow_blank=True)
    payment_mode = serializers.ChoiceField(
        choices=("deposit", "pay_at_hotel", "full"),
        required=False,
        default="deposit",
    )


class CancelHoldSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()


class BulkRateCsvSerializer(serializers.Serializer):
    """CSV body: date,room_type_code,price_1,price_2,price_3,price_4"""

    csv = serializers.CharField()

