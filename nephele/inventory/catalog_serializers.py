from rest_framework import serializers

from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability


class RoomTypeSerializer(serializers.ModelSerializer):
    physical_room_count = serializers.SerializerMethodField()

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
            "physical_room_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "physical_room_count", "created_at", "updated_at"]

    def get_physical_room_count(self, obj) -> int:
        from inventory.services import physical_room_count

        return physical_room_count(obj)


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


class DayAvailabilitySerializer(serializers.Serializer):
    """Per-night patch used by the availability calendar UI."""

    date = serializers.DateField()
    allotment = serializers.IntegerField(required=False, min_value=0)
    stop_sell = serializers.BooleanField(required=False)
    closed = serializers.BooleanField(required=False)
    min_stay = serializers.IntegerField(required=False, min_value=1)
    max_stay = serializers.IntegerField(required=False, min_value=0)
    cta = serializers.BooleanField(required=False)
    ctd = serializers.BooleanField(required=False)
    staff_override = serializers.BooleanField(required=False)


class BulkAvailabilitySerializer(serializers.Serializer):
    """
    Bulk availability upsert body.

    Accepts either:
    - Flat range: ``date_from`` / ``date_to`` plus shared fields applied to each night
    - Per-day list: ``days`` as ``[{date, allotment?, min_stay?, stop_sell?, ...}, ...]``

    ``date_from`` / ``date_to`` may accompany ``days`` (calendar UI sends both).
    """

    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    days = DayAvailabilitySerializer(many=True, required=False)
    allotment = serializers.IntegerField(required=False, min_value=0)
    stop_sell = serializers.BooleanField(required=False)
    closed = serializers.BooleanField(required=False)
    min_stay = serializers.IntegerField(required=False, min_value=1)
    max_stay = serializers.IntegerField(required=False, min_value=0)
    cta = serializers.BooleanField(required=False)
    ctd = serializers.BooleanField(required=False)
    staff_override = serializers.BooleanField(required=False, default=True)

    def validate(self, data):
        days = data.get("days") or []
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        if days:
            return data
        if not date_from or not date_to:
            raise serializers.ValidationError(
                "Provide date_from and date_to, or a non-empty days list."
            )
        if date_to <= date_from:
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
    hold_token = serializers.CharField(required=False, allow_blank=True, default="")
    payment_ref = serializers.CharField(required=False, allow_blank=True)
    payment_mode = serializers.ChoiceField(
        choices=("deposit", "pay_at_hotel", "full"),
        required=False,
        allow_null=True,
        default=None,
    )


class CancelHoldSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    hold_token = serializers.CharField(required=False, allow_blank=True, default="")


class ModifyHoldSerializer(serializers.Serializer):
    PAYMENT_MODE_CHOICES = (
        ("deposit", "Deposit"),
        ("pay_at_hotel", "Pay at hotel"),
        ("full", "Pay in full"),
    )

    hold_token = serializers.CharField(required=False, allow_blank=True, default="")
    check_in = serializers.DateField(required=False)
    check_out = serializers.DateField(required=False)
    adults = serializers.IntegerField(required=False, min_value=1)
    children = serializers.IntegerField(required=False, min_value=0)
    room_type_id = serializers.IntegerField(required=False)
    rate_plan_id = serializers.IntegerField(required=False)
    payment_mode = serializers.ChoiceField(
        choices=PAYMENT_MODE_CHOICES, required=False
    )

    def validate(self, data):
        check_in = data.get("check_in")
        check_out = data.get("check_out")
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in")
        return data


class BulkRateCsvSerializer(serializers.Serializer):
    """CSV body: date,room_type_code,price_1,price_2,price_3,price_4"""

    csv = serializers.CharField()

