# HMS/tests/e2e/test_receptionist_e2e.py
import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import do_login

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.fixture(autouse=True)
def logged_in_as_receptionist(page, base_url, receptionist_credentials):
    do_login(
        page,
        base_url,
        receptionist_credentials["username"],
        receptionist_credentials["password"],
    )
    page.wait_for_url(f"{base_url}/receptionist/dashboard")


class TestReceptionistDashboard:
    def test_dashboard_loads(self, page, base_url):
        expect(page).to_have_url(f"{base_url}/receptionist/dashboard")

    def test_branding_visible(self, page):
        expect(page.get_by_text("NEPHELE HMS")).to_be_visible()


class TestCheckInPage:
    @pytest.fixture(autouse=True)
    def navigate_to_check_in(self, page, base_url):
        page.goto(f"{base_url}/receptionist/check-in")

    def test_heading_visible(self, page):
        expect(page.get_by_text("Check-In / Check-Out")).to_be_visible()

    def test_booking_id_field_visible(self, page):
        expect(page.get_by_label("Booking ID")).to_be_visible()

    def test_lookup_button_visible(self, page):
        expect(page.get_by_role("button", name="Look Up")).to_be_visible()

    def test_lookup_nonexistent_booking_shows_error(self, page):
        page.get_by_label("Booking ID").fill("999999")
        page.get_by_role("button", name="Look Up").click()
        expect(page.locator(".MuiAlert-root")).to_be_visible(timeout=8000)

    def test_empty_lookup_field_does_not_submit(self, page):
        page.get_by_role("button", name="Look Up").click()
        expect(page.get_by_label("Booking ID")).to_be_visible()
