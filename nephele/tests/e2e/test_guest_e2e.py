# nephele/tests/e2e/test_guest_e2e.py
import pytest

pytest.importorskip("playwright")
from playwright.sync_api import expect

from tests.e2e.conftest import do_login

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.fixture(autouse=True)
def logged_in_as_guest(page, base_url, guest_credentials):
    do_login(
        page,
        base_url,
        guest_credentials["username"],
        guest_credentials["password"],
    )
    page.wait_for_url(f"{base_url}/guest/dashboard", timeout=15000)


class TestGuestDashboard:
    def test_welcome_message_visible(self, page):
        expect(page.get_by_text("Welcome,", exact=False)).to_be_visible()

    def test_upcoming_stays_section_visible(self, page):
        expect(page.get_by_text("Upcoming stays")).to_be_visible()

    def test_empty_or_populated_bookings(self, page):
        no_bookings = page.get_by_text("No upcoming stays")
        booking_card = page.locator(".MuiCard-root").first
        assert no_bookings.is_visible() or booking_card.is_visible()

    def test_navigate_to_bookings_via_view_all(self, page, base_url):
        page.get_by_role("button", name="View all").click()
        expect(page).to_have_url(f"{base_url}/guest/bookings")

    def test_my_stays_quick_link(self, page, base_url):
        page.get_by_text("My stays").click()
        expect(page).to_have_url(f"{base_url}/guest/bookings")
