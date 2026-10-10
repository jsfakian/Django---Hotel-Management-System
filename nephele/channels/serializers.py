"""Serializers for Channel Integration API"""

from rest_framework import serializers

from .models import Channel, ChannelBooking


class ChannelSerializer(serializers.ModelSerializer):
    """Channel configuration serializer — credentials write-only / masked on read."""

    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_secret = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True
    )
    api_key_masked = serializers.SerializerMethodField(read_only=True)
    property_name = serializers.CharField(source="property.name", read_only=True)

    class Meta:
        model = Channel
        fields = [
            "id",
            "property",
            "property_name",
            "channel_name",
            "channel_type",
            "account_id",
            "api_key",
            "api_secret",
            "api_key_masked",
            "is_active",
            "sync_enabled",
            "accept_bookings",
            "mapping_config",
            "last_sync_at",
            "last_error",
            "error_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "last_sync_at",
            "last_error",
            "error_count",
            "created_at",
            "updated_at",
            "api_key_masked",
            "property_name",
        ]

    def get_api_key_masked(self, obj):
        return obj.get_readable_api_key() if obj.api_key else ""

    def create(self, validated_data):
        if not validated_data.get("api_key"):
            raise serializers.ValidationError({"api_key": "Required on create"})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Omit blank credential updates so we don't wipe existing secrets
        if validated_data.get("api_key") in (None, ""):
            validated_data.pop("api_key", None)
        if validated_data.get("api_secret") in (None, ""):
            validated_data.pop("api_secret", None)
        return super().update(instance, validated_data)


class ChannelDetailSerializer(ChannelSerializer):
    """Detailed channel serializer with mapping config (same fields)."""

    class Meta(ChannelSerializer.Meta):
        pass


class ChannelBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelBooking
        fields = [
            "id",
            "channel",
            "channel_booking_id",
            "nephele_booking",
            "sync_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChannelBookingReceiptSerializer(serializers.Serializer):
    channel_booking_id = serializers.CharField(max_length=255)
    timestamp = serializers.IntegerField()
    event = serializers.CharField(default="booking_created")

    guest_first_name = serializers.CharField(max_length=100)
    guest_last_name = serializers.CharField(max_length=100)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, required=False)

    room_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    number_of_guests = serializers.IntegerField()
    special_requests = serializers.CharField(required=False, allow_blank=True)

    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default="EUR")

    def validate(self, data):
        if data["check_out"] <= data["check_in"]:
            raise serializers.ValidationError("Check-out must be after check-in")
        if data["number_of_guests"] < 1:
            raise serializers.ValidationError("Number of guests must be at least 1")
        return data


class ChannelAvailabilityStatusSerializer(serializers.Serializer):
    channel_name = serializers.CharField(read_only=True)
    property_id = serializers.IntegerField(read_only=True)
    last_sync_at = serializers.DateTimeField(read_only=True)
    sync_status = serializers.CharField(read_only=True)
    rooms_synced = serializers.IntegerField(read_only=True)
    pending_sync_count = serializers.IntegerField(read_only=True)
    last_error = serializers.CharField(read_only=True, allow_null=True)


class ChannelAvailabilitySyncSerializer(serializers.Serializer):
    SYNC_TYPE_CHOICES = (
        ("full_sync", "Full Synchronization"),
        ("incremental_sync", "Incremental Sync"),
        ("date_range", "Date Range Sync"),
    )

    sync_type = serializers.ChoiceField(choices=SYNC_TYPE_CHOICES, default="full_sync")
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    override_staff = serializers.BooleanField(default=False)

    def validate(self, data):
        if data.get("sync_type") == "date_range":
            if not data.get("date_from") or not data.get("date_to"):
                raise serializers.ValidationError(
                    "date_from and date_to required for date_range sync type"
                )
            if data["date_to"] <= data["date_from"]:
                raise serializers.ValidationError("date_to must be after date_from")
        return data
