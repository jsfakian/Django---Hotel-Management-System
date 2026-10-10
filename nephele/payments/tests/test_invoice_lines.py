"""Invoice line item builder tests."""

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from payments.invoice_lines import booking_invoice_lines


@pytest.mark.unit
def test_booking_invoice_lines_include_vat_and_climate():
    booking = SimpleNamespace(
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        base_price=Decimal("200.00"),
        vat_amount=Decimal("26.00"),
        climate_resilience_fee=Decimal("3.00"),
        actual_price=Decimal("229.00"),
        room_type=SimpleNamespace(name="Sea View"),
        room_type_id=1,
        room_id=None,
    )
    lines = booking_invoice_lines(booking)
    codes = {l["code"] for l in lines}
    assert codes >= {"ROOM", "VAT", "CLIMATE"}
    assert sum(l["amount"] for l in lines) == Decimal("229.00")
