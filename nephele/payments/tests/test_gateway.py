# nephele/payments/tests/test_gateway.py
"""Unit tests for payment gateways and MyData sandbox/live branches."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from payments.gateway import (
    PaymentGatewayError,
    StripeGateway,
    VivaWalletGateway,
    get_payment_gateway,
)


@pytest.mark.unit
def test_viva_demo_without_credentials(settings):
    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    gw = VivaWalletGateway()
    result = gw.create_payment(amount=Decimal("25.00"), description="Test")
    assert result["demo"] is True
    assert result["gateway"] == "viva"
    assert result["payment_id"].startswith("viva-demo-")
    assert result["status"] == "pending"


@pytest.mark.unit
def test_stripe_stub_without_secret(settings):
    settings.STRIPE_SECRET_KEY = ""
    gw = StripeGateway()
    result = gw.create_payment(amount=Decimal("10.00"))
    assert result.get("demo") is True or result.get("status") in ("pending", "stub")
    assert result["gateway"] == "stripe"


@pytest.mark.unit
def test_get_payment_gateway_defaults_to_viva(settings):
    settings.DEFAULT_PAYMENT_GATEWAY = "viva"
    assert isinstance(get_payment_gateway(), VivaWalletGateway)


@pytest.mark.unit
def test_get_payment_gateway_stripe(settings):
    settings.DEFAULT_PAYMENT_GATEWAY = "stripe"
    assert isinstance(get_payment_gateway("stripe"), StripeGateway)


@pytest.mark.unit
def test_viva_http_create_payment(settings):
    settings.VIVA_MERCHANT_ID = "merchant"
    settings.VIVA_API_KEY = "secret"
    settings.VIVA_API_BASE = "https://demo-api.vivapayments.com"
    gw = VivaWalletGateway()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"orderCode": 999}'
    mock_resp.json.return_value = {"orderCode": 999}
    with patch("payments.gateway.requests.post", return_value=mock_resp) as post:
        result = gw.create_payment(amount=Decimal("12.50"), currency="EUR")
    assert result["payment_id"] == "999"
    assert result["gateway"] == "viva"
    post.assert_called_once()


@pytest.mark.unit
def test_viva_http_error_raises(settings):
    settings.VIVA_MERCHANT_ID = "merchant"
    settings.VIVA_API_KEY = "secret"
    gw = VivaWalletGateway()
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = '{"error":"bad"}'
    mock_resp.json.return_value = {"error": "bad"}
    with patch("payments.gateway.requests.post", return_value=mock_resp):
        with pytest.raises(PaymentGatewayError):
            gw.create_payment(amount=Decimal("1.00"))


@pytest.mark.unit
def test_viva_verify_demo_payment(settings):
    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    gw = VivaWalletGateway()
    created = gw.create_payment(amount=Decimal("5.00"))
    verified = gw.verify_payment(created["payment_id"])
    assert verified["paid"] is True


@pytest.mark.unit
def test_mydata_sandbox_poll_status(settings):
    settings.HOTEL_TAX_ID = "123456789"
    settings.MYDATA_SANDBOX_MODE = True
    from payments.mydata_service import MyDataService

    svc = MyDataService()
    result = svc.poll_status("AADE-TEST-1")
    assert result["status"] == "accepted"
    assert result["sandbox"] is True


@pytest.mark.unit
def test_mydata_live_requires_credentials(settings):
    settings.HOTEL_TAX_ID = "123456789"
    settings.MYDATA_SANDBOX_MODE = False
    settings.MYDATA_USERNAME = ""
    settings.MYDATA_SUBSCRIPTION_KEY = ""
    settings.MYDATA_API_KEY = ""
    from payments.mydata_service import MyDataService, MyDataServiceException

    svc = MyDataService()
    with pytest.raises(MyDataServiceException):
        svc.poll_status("MARK-1")


@pytest.mark.unit
def test_mydata_live_poll_status_request_docs_get(settings):
    settings.HOTEL_TAX_ID = "123456789"
    settings.MYDATA_SANDBOX_MODE = False
    settings.MYDATA_USERNAME = "user"
    settings.MYDATA_SUBSCRIPTION_KEY = "sub-key"
    settings.MYDATA_API_BASE = "https://mydata.test/api"
    from payments.mydata_service import MyDataService

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"status":"accepted"}'
    mock_resp.json.return_value = {"status": "accepted"}
    svc = MyDataService()
    with patch("payments.mydata_service.requests.get", return_value=mock_resp) as get:
        result = svc.poll_status("MARK-42")
    assert result["transmission_id"] == "MARK-42"
    assert result["status"] == "accepted"
    assert result["sandbox"] is False
    get.assert_called_once()
    args, kwargs = get.call_args
    assert args[0] == "https://mydata.test/api/RequestDocs"
    assert kwargs["params"] == {"mark": "MARK-42"}
    assert kwargs["headers"]["aade-user-id"] == "user"
    assert kwargs["headers"]["Ocp-Apim-Subscription-Key"] == "sub-key"


@pytest.mark.unit
def test_mydata_requires_tax_id(settings):
    settings.HOTEL_TAX_ID = ""
    from payments.mydata_service import MyDataService

    with pytest.raises(ImproperlyConfigured):
        MyDataService()


@pytest.mark.unit
@pytest.mark.django_db
def test_mydata_export_includes_aade_header_and_details(settings):
    """Sandbox export carries invoiceHeader / invoiceDetails / issuer AFM."""
    from datetime import timedelta

    from django.contrib.auth.models import User
    from django.utils import timezone

    from accounts.models import Guest
    from payments.models import Invoice, Payment, PaymentMethod
    from payments.mydata_service import MyDataService

    settings.HOTEL_TAX_ID = "999999999"
    settings.MYDATA_SANDBOX_MODE = True
    user = User.objects.create_user(
        username="aade_guest", email="aade@example.com", first_name="A", last_name="B"
    )
    guest = Guest.objects.create(
        user=user,
        email=user.email,
        first_name="A",
        last_name="B",
        preferences={"afm": "111222333"},
    )
    pm = PaymentMethod.objects.create(
        name="AADE Export Card", payment_type="card", is_active=True
    )
    payment = Payment.objects.create(
        guest=guest,
        payment_method=pm,
        amount=Decimal("100.00"),
        currency="EUR",
        transaction_id="TX-AADE-1",
        reference_code="REF-AADE-1",
    )
    invoice = Invoice.objects.create(
        guest=guest,
        payment=payment,
        amount=Decimal("100.00"),
        tax_amount=Decimal("24.00"),
        total_amount=Decimal("124.00"),
        status="issued",
        description="Stay",
        due_date=timezone.now().date() + timedelta(days=30),
    )
    svc = MyDataService()
    exported = svc.export_invoice(invoice)
    inv = exported["invoice"]
    assert inv["issuer"]["afm"] == "999999999"
    assert inv["counterpart"]["afm"] == "111222333"
    assert "invoiceHeader" in inv
    assert inv["invoiceHeader"]["currency"] == "EUR"
    assert inv["invoiceDetails"]
    assert "vatCategory" in inv["invoiceDetails"][0]
    assert "netValue" in inv["invoiceDetails"][0]


@pytest.mark.unit
@pytest.mark.django_db
def test_mydata_live_transmit_posts_aade_invoices_doc(settings):
    """Live mode POSTs InvoicesDoc with AADE field names, not a bare stub."""
    from datetime import timedelta

    from django.contrib.auth.models import User
    from django.utils import timezone

    from accounts.models import Guest
    from payments.models import Invoice, Payment, PaymentMethod
    from payments.mydata_service import MyDataService

    settings.HOTEL_TAX_ID = "999999999"
    settings.MYDATA_SANDBOX_MODE = False
    settings.MYDATA_USERNAME = "user"
    settings.MYDATA_SUBSCRIPTION_KEY = "sub-key"
    settings.MYDATA_API_BASE = "https://mydata.test/api"
    user = User.objects.create_user(
        username="live_aade", email="live@example.com", first_name="L", last_name="I"
    )
    guest = Guest.objects.create(
        user=user, email=user.email, first_name="L", last_name="I"
    )
    pm = PaymentMethod.objects.create(
        name="AADE Live Card", payment_type="card", is_active=True
    )
    payment = Payment.objects.create(
        guest=guest,
        payment_method=pm,
        amount=Decimal("50.00"),
        currency="EUR",
        transaction_id="TX-LIVE-1",
        reference_code="REF-LIVE-1",
    )
    invoice = Invoice.objects.create(
        guest=guest,
        payment=payment,
        amount=Decimal("50.00"),
        tax_amount=Decimal("12.00"),
        total_amount=Decimal("62.00"),
        status="issued",
        description="Live stay",
        due_date=timezone.now().date() + timedelta(days=30),
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"mark":"MARK-99"}'
    mock_resp.json.return_value = {"mark": "MARK-99"}
    svc = MyDataService()
    with patch("payments.mydata_service.requests.post", return_value=mock_resp) as post:
        ok, mark = svc.transmit_invoice(invoice)
    assert ok is True
    assert mark == "MARK-99"
    post.assert_called_once()
    _args, kwargs = post.call_args
    payload = kwargs["json"]
    assert "InvoicesDoc" in payload
    node = payload["InvoicesDoc"]["invoice"][0]
    assert "invoiceHeader" in node
    assert "invoiceDetails" in node
    assert node["issuer"]["vatNumber"] == "999999999"
    assert node["invoiceDetails"][0]["vatCategory"] == "1"
    assert "netValue" in node["invoiceDetails"][0]
    assert "vatAmount" in node["invoiceDetails"][0]
    assert "xml" in payload
    invoice.refresh_from_db()
    assert invoice.mydata_transmitted is True


@pytest.mark.unit
def test_start_booking_checkout_returns_api_fields(settings):
    from payments.gateway import start_booking_checkout

    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    settings.DEFAULT_PAYMENT_GATEWAY = "viva"
    result = start_booking_checkout(
        amount=Decimal("30.00"),
        booking_id=42,
        customer_email="guest@example.com",
        description="Deposit",
    )
    assert result["payment_ref"].startswith("viva-demo-")
    assert result["checkout_url"]
    assert "client_secret" in result
    assert result["gateway"] == "viva"


@pytest.mark.unit
@pytest.mark.django_db
def test_hold_dict_includes_checkout_for_deposit(settings):
    """create_hold + hold_booking_dict expose gateway fields for deposit."""
    from datetime import date, timedelta
    from decimal import Decimal as D

    from inventory.booking_engine import create_hold, hold_booking_dict
    from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
    from properties.models import Property

    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    prop = Property.objects.create(
        name="Pay Hotel",
        location="Athens",
        address="1",
        city="Athens",
        postal_code="10000",
        country="GR",
    )
    rt = RoomType.objects.create(
        property=prop,
        name="Double",
        code="DBL",
        capacity=2,
        max_occupancy=2,
        base_price=D("100.00"),
    )
    rp = RatePlan.objects.create(
        property=prop, name="BAR", code="BAR", meal_plan="RO"
    )
    rp.room_types.add(rt)
    check_in = date.today() + timedelta(days=10)
    check_out = check_in + timedelta(days=2)
    for d in (check_in, check_in + timedelta(days=1)):
        RoomTypeAvailability.objects.create(
            room_type=rt, date=d, allotment=3, booked=0
        )
        RatePlanPrice.objects.create(
            rate_plan=rp,
            room_type=rt,
            date=d,
            price_1=D("100.00"),
            price_2=D("100.00"),
        )
    booking = create_hold(
        property_id=prop.id,
        room_type_id=rt.id,
        rate_plan_id=rp.id,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        guest_email="deposit@example.com",
        guest_first_name="Dep",
        guest_last_name="Osit",
        payment_mode="deposit",
    )
    payload = hold_booking_dict(booking)
    assert payload["payment_mode"] == "deposit"
    assert payload.get("checkout_url")
    assert payload.get("payment_ref")

    hotel_pay = create_hold(
        property_id=prop.id,
        room_type_id=rt.id,
        rate_plan_id=rp.id,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        guest_email="athotel@example.com",
        guest_first_name="At",
        guest_last_name="Hotel",
        payment_mode="pay_at_hotel",
    )
    hotel_payload = hold_booking_dict(hotel_pay)
    assert not hotel_payload.get("checkout_url")
    assert not hotel_payload.get("payment_ref")
