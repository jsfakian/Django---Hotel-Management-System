# HMS/tests/e2e/test_auth_e2e.py
import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import do_login

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestLoginPage:
    def test_login_page_renders(self, page, base_url):
        page.goto(f"{base_url}/login")
        expect(page.get_by_text("NEPHELE HMS")).to_be_visible()
        expect(page.get_by_label("Username or Email")).to_be_visible()
        expect(page.get_by_label("Password")).to_be_visible()
        expect(page.get_by_role("button", name="Sign In")).to_be_visible()

    def test_login_shows_forgot_password_link(self, page, base_url):
        page.goto(f"{base_url}/login")
        expect(page.get_by_role("link", name="Forgot password?")).to_be_visible()

    def test_login_with_invalid_credentials_shows_error(self, page, base_url):
        page.goto(f"{base_url}/login")
        page.get_by_label("Username or Email").fill("notauser")
        page.get_by_label("Password").fill("wrongpassword")
        page.get_by_role("button", name="Sign In").click()
        expect(page.locator(".MuiAlert-root")).to_be_visible(timeout=5000)

    def test_protected_route_redirects_unauthenticated(self, page, base_url):
        page.goto(f"{base_url}/guest/dashboard")
        expect(page).to_have_url(f"{base_url}/login")


class TestRoleRedirects:
    def test_login_as_guest_redirects_to_dashboard(
        self, page, base_url, guest_credentials
    ):
        do_login(
            page,
            base_url,
            guest_credentials["username"],
            guest_credentials["password"],
        )
        expect(page).to_have_url(f"{base_url}/guest/dashboard", timeout=10000)

    def test_login_as_receptionist_redirects_to_dashboard(
        self, page, base_url, receptionist_credentials
    ):
        do_login(
            page,
            base_url,
            receptionist_credentials["username"],
            receptionist_credentials["password"],
        )
        expect(page).to_have_url(
            f"{base_url}/receptionist/dashboard", timeout=10000
        )

    def test_login_as_manager_redirects_to_dashboard(
        self, page, base_url, manager_credentials
    ):
        do_login(
            page,
            base_url,
            manager_credentials["username"],
            manager_credentials["password"],
        )
        expect(page).to_have_url(f"{base_url}/manager/dashboard", timeout=10000)
