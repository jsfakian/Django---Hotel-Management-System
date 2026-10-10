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
from inventory.booking_engine import (
    cancel_hold,
    confirm_hold,
    create_hold,
    hold_booking_dict,
    modify_hold,
    quote,
)
from inventory.catalog_serializers import (
    AvailabilityQuoteSerializer,
    BulkAvailabilitySerializer,
    BulkRateCsvSerializer,
    CancelHoldSerializer,
    ConfirmHoldSerializer,
    HoldBookingSerializer,
    ModifyHoldSerializer,
    RatePlanSerializer,
    RoomTypeAvailabilitySerializer,
    RoomTypeSerializer,
)
from inventory.models import (
    RatePlan,
    RatePlanPrice,
    RoomType,
    RoomTypeAvailability,
    RoomTypeAvailabilityAudit,
)
from inventory.services import daterange, ensure_room_type_availability
from room.models import Booking, Room


_AVAIL_PATCH_FIELDS = (
    "allotment",
    "stop_sell",
    "closed",
    "min_stay",
    "max_stay",
    "cta",
    "ctd",
    "staff_override",
)


def _record_availability_audit(avail, data, user, note=""):
    """Write audit row when staff changes allotment or staff_override."""
    new_allotment = data.get("allotment", avail.allotment)
    new_override = data.get("staff_override", avail.staff_override)
    if new_allotment == avail.allotment and new_override == avail.staff_override:
        return
    RoomTypeAvailabilityAudit.objects.create(
        room_type=avail.room_type,
        date=avail.date,
        old_allotment=avail.allotment,
        new_allotment=new_allotment,
        old_staff_override=avail.staff_override,
        new_staff_override=new_override,
        changed_by=user if user and user.is_authenticated else None,
        note=note or "",
    )


def _apply_availability_patch(avail, data, user):
    _record_availability_audit(avail, data, user)
    for field in _AVAIL_PATCH_FIELDS:
        if field in data:
            setattr(avail, field, data[field])
    if user and user.is_authenticated:
        avail.updated_by = user
    avail.save()
    return avail


def _availability_update_rows(data):
    """Yield (night_date, patch_dict) from flat range or days[] payload."""
    days = data.get("days") or []
    if days:
        for day in days:
            patch = {k: day[k] for k in _AVAIL_PATCH_FIELDS if k in day}
            yield day["date"], patch
        return
    shared = {k: data[k] for k in _AVAIL_PATCH_FIELDS if k in data}
    for night in daterange(data["date_from"], data["date_to"]):
        yield night, shared


def _list_room_type_availability(room_type, query_params):
    """
    Existing RoomTypeAvailability rows for calendar GET.

    Query: date_from (inclusive ISO), date_to (exclusive ISO).
    Response: list of {
      id, room_type, date, allotment, booked, stop_sell, closed,
      min_stay, max_stay, cta, ctd, staff_override, updated_by,
      restrictions, available_units
    }
    """
    qs = RoomTypeAvailability.objects.filter(room_type=room_type).order_by("date")
    date_from = query_params.get("date_from")
    date_to = query_params.get("date_to")
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lt=date_to)
    return RoomTypeAvailabilitySerializer(qs, many=True).data


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
        """
        GET calendar rows / PATCH bulk upsert for a room type.

        GET query: ``date_from`` (inclusive), ``date_to`` (exclusive).
        GET response: array of RoomTypeAvailabilitySerializer objects
        (id, room_type, date, allotment, booked, stop_sell, closed, min_stay,
        max_stay, cta, ctd, staff_override, updated_by, restrictions,
        available_units).

        PATCH body: flat ``date_from``/``date_to`` + shared fields, or
        ``days: [{date, allotment?, min_stay?, stop_sell?, ...}]``.
        """
        room_type = self.get_object()
        if request.method == "GET":
            return Response(
                _list_room_type_availability(room_type, request.query_params)
            )

        ser = BulkAvailabilitySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        updated = [
            _apply_availability_patch(
                ensure_room_type_availability(room_type, night),
                patch,
                request.user,
            )
            for night, patch in _availability_update_rows(data)
        ]
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
        return Response(hold_booking_dict(booking), status=status.HTTP_201_CREATED)


def _checkout_before_confirm(booking_id, payment_mode, payment_ref):
    """Start gateway checkout for deposit/full when no payment_ref yet."""
    if payment_ref or payment_mode == "pay_at_hotel":
        return {}, payment_ref
    from inventory.booking_engine import gateway_checkout_for_booking

    held = Booking.objects.filter(pk=booking_id).first()
    if held is None:
        return {}, payment_ref
    checkout = gateway_checkout_for_booking(held, payment_mode)
    return checkout, checkout.get("payment_ref") or payment_ref


def _confirm_response(booking, payment_mode, checkout):
    body = {
        "booking_id": booking.id,
        "status": booking.status,
        "confirmation_number": f"NEPH-{booking.id}",
        "check_in": booking.check_in_date,
        "check_out": booking.check_out_date,
        "total": str(booking.actual_price),
        "payment_mode": payment_mode or getattr(booking, "payment_mode", None),
    }
    if checkout:
        body.update(checkout)
    return Response(body)


class BookingEngineConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from inventory.booking_engine import HoldExpiredError, HoldNotFoundError

        ser = ConfirmHoldSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payment_mode = ser.validated_data.get("payment_mode")
        payment_ref = ser.validated_data.get("payment_ref") or None
        booking_id = ser.validated_data["booking_id"]
        checkout, payment_ref = _checkout_before_confirm(
            booking_id, payment_mode, payment_ref
        )
        try:
            booking = confirm_hold(
                booking_id, payment_ref=payment_ref, payment_mode=payment_mode
            )
        except HoldNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except HoldExpiredError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_410_GONE)
        except Booking.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return _confirm_response(booking, payment_mode, checkout)


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


class BookingEngineModifyHoldView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, booking_id):
        ser = ModifyHoldSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            from inventory.booking_engine import (
                BookingEngineError,
                HoldExpiredError,
                HoldNotFoundError,
                NoAllotmentError,
            )

            payload = modify_hold(booking_id, **ser.validated_data)
        except HoldNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except HoldExpiredError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_410_GONE)
        except NoAllotmentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_409_CONFLICT)
        except BookingEngineError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payload)


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


def _guest_display_name(booking):
    if booking.guest_id:
        return f"{booking.guest.first_name} {booking.guest.last_name}"
    return None


def _booking_on_night(bookings, room_id, night):
    return next(
        (
            b
            for b in bookings
            if b.room_id == room_id and b.check_in_date <= night < b.check_out_date
        ),
        None,
    )


def _tape_chart_cells(room, bookings, d0, d1):
    cells = []
    for night in daterange(d0, d1):
        hit = _booking_on_night(bookings, room.id, night)
        cells.append(
            {
                "date": night.isoformat(),
                "booking_id": hit.id if hit else None,
                "status": hit.status if hit else room.status,
                "guest": _guest_display_name(hit) if hit else None,
            }
        )
    return cells


def _tape_chart_room_rows(rooms, bookings, d0, d1):
    return [
        {
            "room_id": room.id,
            "room_number": room.room_number,
            "status": room.status,
            "room_type_fk": room.room_type_fk_id,
            "cells": _tape_chart_cells(room, bookings, d0, d1),
        }
        for room in rooms
    ]


def _tape_chart_unassigned(unassigned):
    return [
        {
            "booking_id": b.id,
            "room_type": b.room_type_id,
            "check_in": b.check_in_date,
            "check_out": b.check_out_date,
            "status": b.status,
            "guest": _guest_display_name(b),
        }
        for b in unassigned
    ]


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
    bookings = list(
        Booking.objects.filter(
            room__property_id=property_id,
            status__in=["pending", "confirmed", "checked_in", "held"],
            check_in_date__lt=d1,
            check_out_date__gt=d0,
        ).select_related("guest", "room_type")
    )
    unassigned = Booking.objects.filter(
        room__isnull=True,
        room_type__property_id=property_id,
        status__in=["pending", "confirmed", "held"],
        check_in_date__lt=d1,
        check_out_date__gt=d0,
    ).select_related("guest", "room_type")

    return Response(
        {
            "rooms": _tape_chart_room_rows(rooms, bookings, d0, d1),
            "unassigned": _tape_chart_unassigned(unassigned),
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
