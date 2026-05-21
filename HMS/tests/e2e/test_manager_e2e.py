# HMS/tests/e2e/test_manager_e2e.py
import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import do_login

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.fixture(autouse=True)
def logged_in_as_manager(page, base_url, manager_credentials):
    do_login(
        page,
        base_url,
        manager_credentials["username"],
        manager_credentials["password"],
    )
    page.wait_for_url(f"{base_url}/manager/dashboard")


class TestManagerDashboard:
    def test_dashboard_url_correct(self, page, base_url):
        expect(page).to_have_url(f"{base_url}/manager/dashboard")

    def test_branding_visible(self, page):
        expect(page.get_by_text("NEPHELE HMS")).to_be_visible()

    def test_manager_cannot_access_admin_dashboard(self, page, base_url):
        page.goto(f"{base_url}/admin/dashboard")
        assert page.url != f"{base_url}/admin/dashboard"
