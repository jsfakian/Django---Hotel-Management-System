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
def test_mydata_requires_tax_id(settings):
    settings.HOTEL_TAX_ID = ""
    from payments.mydata_service import MyDataService

    with pytest.raises(ImproperlyConfigured):
        MyDataService()
