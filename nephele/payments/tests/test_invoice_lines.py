"""Invoice line item builder tests."""

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from payments.invoice_lines import (
    apply_invoice_lines,
    attach_lines_to_invoice_description,
    booking_invoice_lines,
)


@pytest.fixture
def sample_booking():
    return SimpleNamespace(
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


@pytest.mark.unit
def test_booking_invoice_lines_include_vat_and_climate(sample_booking):
    lines = booking_invoice_lines(sample_booking)
    codes = {l["code"] for l in lines}
    assert codes >= {"ROOM", "VAT", "CLIMATE"}
    assert sum(l["amount"] for l in lines) == Decimal("229.00")


@pytest.mark.unit
def test_attach_lines_and_apply_to_invoice(sample_booking):
    desc = attach_lines_to_invoice_description(None, sample_booking)
    assert "Sea View" in desc
    assert "VAT" in desc or "ΦΠΑ" in desc

    invoice = SimpleNamespace(notes="Auto-created", line_items=None, description="")
    lines = apply_invoice_lines(invoice, sample_booking)
    assert invoice.line_items
    assert invoice.line_items[0]["code"] == "ROOM"
    assert "line_items" in invoice.notes
    assert len(lines) >= 3


@pytest.mark.unit
def test_ensure_invoice_lines_skips_when_present(sample_booking):
    from payments.invoice_lines import ensure_invoice_lines

    invoice = SimpleNamespace(
        notes="",
        line_items=[{"code": "ROOM"}],
        description="x",
        booking=sample_booking,
    )
    out = ensure_invoice_lines(invoice)
    assert out == [{"code": "ROOM"}]
    forced = ensure_invoice_lines(invoice, force=True)
    assert forced[0]["code"] == "ROOM"
    assert len(invoice.line_items) >= 3
