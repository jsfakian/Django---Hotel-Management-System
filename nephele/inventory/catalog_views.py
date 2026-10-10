"""Room types, rate plans, quote, booking-engine, front-desk APIs."""

from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api_permissions import IsHotelStaff
from inventory.booking_engine import cancel_hold, confirm_hold, create_hold, quote
from inventory.catalog_serializers import (
    AvailabilityQuoteSerializer,
    BulkAvailabilitySerializer,
    BulkRateCsvSerializer,
    CancelHoldSerializer,
    ConfirmHoldSerializer,
    HoldBookingSerializer,
    RatePlanSerializer,
    RoomTypeAvailabilitySerializer,
    RoomTypeSerializer,
)
from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
from inventory.services import daterange, ensure_room_type_availability
from room.models import Booking, Room


class RoomTypeViewSet(viewsets.ModelViewSet):
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["property", "is_active", "code"]
    search_fields = ["code", "name"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "availability"):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return RoomType.objects.select_related("property").all()

    @action(detail=True, methods=["get", "patch"], url_path="availability")
    def availability(self, request, pk=None):
        room_type = self.get_object()
        if request.method == "GET":
            date_from = request.query_params.get("date_from")
            date_to = request.query_params.get("date_to")
            qs = RoomTypeAvailability.objects.filter(room_type=room_type)
            if date_from:
                qs = qs.filter(date__gte=date_from)
            if date_to:
                qs = qs.filter(date__lt=date_to)
            return Response(RoomTypeAvailabilitySerializer(qs, many=True).data)

        ser = BulkAvailabilitySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        updated = []
        for night in daterange(data["date_from"], data["date_to"]):
            avail = ensure_room_type_availability(room_type, night)
            for field in (
                "allotment",
                "stop_sell",
                "closed",
                "min_stay",
                "max_stay",
                "cta",
                "ctd",
                "staff_override",
            ):
                if field in data:
                    setattr(avail, field, data[field])
            if request.user and request.user.is_authenticated:
                avail.updated_by = request.user
            avail.save()
            updated.append(avail)
        return Response(RoomTypeAvailabilitySerializer(updated, many=True).data)


class RatePlanViewSet(viewsets.ModelViewSet):
    serializer_class = RatePlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["property", "is_active", "meal_plan"]
    search_fields = ["code", "name"]

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "bulk_prices",
        ):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return RatePlan.objects.prefetch_related("room_types").all()

    @action(detail=True, methods=["post"], url_path="bulk-prices")
    def bulk_prices(self, request, pk=None):
        """
        Upload nightly rates as CSV text.
        Header: date,room_type_code,price_1,price_2,price_3,price_4
        """
        import csv
        import io
        from datetime import datetime
        from decimal import Decimal, InvalidOperation

        rate_plan = self.get_object()
        ser = BulkRateCsvSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reader = csv.DictReader(io.StringIO(ser.validated_data["csv"]))
        upserted = 0
        errors = []
        for i, row in enumerate(reader, start=2):
            try:
                on_date = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
                code = row["room_type_code"].strip()
                room_type = RoomType.objects.get(
                    property_id=rate_plan.property_id, code=code
                )
                defaults = {}
                for key in ("price_1", "price_2", "price_3", "price_4"):
                    raw = (row.get(key) or "").strip()
                    if raw:
                        defaults[key] = Decimal(raw)
                RatePlanPrice.objects.update_or_create(
                    rate_plan=rate_plan,
                    room_type=room_type,
                    date=on_date,
                    defaults=defaults,
                )
                upserted += 1
            except (KeyError, ValueError, InvalidOperation, RoomType.DoesNotExist) as exc:
                errors.append({"line": i, "error": str(exc)})
        return Response({"upserted": upserted, "errors": errors})


class AvailabilityQuoteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = AvailabilityQuoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        results = quote(
            data["property_id"],
            data["check_in"],
            data["check_out"],
            adults=data["adults"],
            children=data["children"],
            children_ages=data.get("children_ages"),
        )
        return Response({"results": results, "count": len(results)})


class BookingEngineHoldView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = HoldBookingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            booking = create_hold(**ser.validated_data)
        except Exception as exc:
            from inventory.booking_engine import BookingEngineError, NoAllotmentError

            code = status.HTTP_400_BAD_REQUEST
            if isinstance(exc, NoAllotmentError):
                code = status.HTTP_409_CONFLICT
            elif not isinstance(exc, (BookingEngineError, ValueError, TypeError)):
                raise
            return Response({"error": str(exc)}, status=code)
        return Response(
            {
                "booking_id": booking.id,
                "status": booking.status,
                "hold_expires_at": booking.hold_expires_at,
                "total": str(booking.actual_price),
                "vat_amount": str(booking.vat_amount),
                "climate_resilience_fee": str(booking.climate_resilience_fee),
                "payment_mode": getattr(booking, "payment_mode", "deposit"),
                "deposit_due": str(
                    getattr(booking, "deposit_due", booking.actual_price)
                ),
                "notes": booking.notes,
            },
            status=status.HTTP_201_CREATED,
        )


class BookingEngineConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ConfirmHoldSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            from inventory.booking_engine import HoldExpiredError, HoldNotFoundError

            booking = confirm_hold(
                ser.validated_data["booking_id"],
                payment_ref=ser.validated_data.get("payment_ref") or None,
                payment_mode=ser.validated_data.get("payment_mode"),
            )
        except HoldNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except HoldExpiredError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_410_GONE)
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "booking_id": booking.id,
                "status": booking.status,
                "confirmation_number": f"NEPH-{booking.id}",
                "check_in": booking.check_in_date,
                "check_out": booking.check_out_date,
                "total": str(booking.actual_price),
            }
        )


class BookingEngineCancelView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = CancelHoldSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            from inventory.booking_engine import BookingEngineError, HoldNotFoundError

            booking = cancel_hold(ser.validated_data["booking_id"])
        except HoldNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except BookingEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"booking_id": booking.id, "status": booking.status})


class BookingEngineConfirmationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id)
        if booking.status == "held" and booking.booking_source != "booking_engine":
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "booking_id": booking.id,
                "status": booking.status,
                "confirmation_number": f"NEPH-{booking.id}",
                "guest_email": getattr(booking.guest, "email", None),
                "check_in": booking.check_in_date,
                "check_out": booking.check_out_date,
                "room_type": booking.room_type_id,
                "rate_plan": booking.rate_plan_id,
                "total": str(booking.actual_price),
                "vat_amount": str(booking.vat_amount or 0),
                "climate_resilience_fee": str(booking.climate_resilience_fee or 0),
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHotelStaff])
def tape_chart(request):
    property_id = request.query_params.get("property_id")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    if not property_id or not date_from or not date_to:
        return Response(
            {"error": "property_id, date_from, date_to required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    from datetime import date as date_cls

    d0 = date_cls.fromisoformat(date_from)
    d1 = date_cls.fromisoformat(date_to)
    rooms = Room.objects.filter(property_id=property_id).order_by("room_number")
    bookings = Booking.objects.filter(
        room__property_id=property_id,
        status__in=["pending", "confirmed", "checked_in", "held"],
        check_in_date__lt=d1,
        check_out_date__gt=d0,
    ).select_related("guest", "room_type")
    unassigned = Booking.objects.filter(
        room__isnull=True,
        room_type__property_id=property_id,
        status__in=["pending", "confirmed", "held"],
        check_in_date__lt=d1,
        check_out_date__gt=d0,
    ).select_related("guest", "room_type")

    room_rows = []
    for room in rooms:
        cells = []
        for night in daterange(d0, d1):
            hit = next(
                (
                    b
                    for b in bookings
                    if b.room_id == room.id
                    and b.check_in_date <= night < b.check_out_date
                ),
                None,
            )
            cells.append(
                {
                    "date": night.isoformat(),
                    "booking_id": hit.id if hit else None,
                    "status": hit.status if hit else room.status,
                    "guest": (
                        f"{hit.guest.first_name} {hit.guest.last_name}"
                        if hit and hit.guest_id
                        else None
                    ),
                }
            )
        room_rows.append(
            {
                "room_id": room.id,
                "room_number": room.room_number,
                "status": room.status,
                "room_type_fk": room.room_type_fk_id,
                "cells": cells,
            }
        )
    return Response(
        {
            "rooms": room_rows,
            "unassigned": [
                {
                    "booking_id": b.id,
                    "room_type": b.room_type_id,
                    "check_in": b.check_in_date,
                    "check_out": b.check_out_date,
                    "status": b.status,
                    "guest": (
                        f"{b.guest.first_name} {b.guest.last_name}" if b.guest_id else None
                    ),
                }
                for b in unassigned
            ],
        }
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsHotelStaff])
def housekeeping_board(request):
    property_id = request.query_params.get("property_id") or request.data.get("property_id")
    qs = Room.objects.all()
    if property_id:
        qs = qs.filter(property_id=property_id)
    if request.method == "GET":
        return Response(
            [
                {
                    "room_id": r.id,
                    "room_number": r.room_number,
                    "status": r.status,
                    "floor": r.floor,
                    "property": r.property_id,
                }
                for r in qs.order_by("floor", "room_number")
            ]
        )
    room_id = request.data.get("room_id")
    new_status = request.data.get("status")
    room = get_object_or_404(Room, pk=room_id)
    if new_status not in dict(Room.STATUS_CHOICES):
        return Response({"error": "invalid status"}, status=status.HTTP_400_BAD_REQUEST)
    room.status = new_status
    room.save(update_fields=["status", "updated_at"])
    return Response({"room_id": room.id, "status": room.status})
