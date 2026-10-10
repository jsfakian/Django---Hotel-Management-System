# nephele/tests/e2e/conftest.py
import os
import time

import pytest
import requests

# Deterministic users created by `python manage.py seed_e2e_users`.
E2E_USERS = {
    "guest": {"username": "e2e_guest", "password": "E2eGuest!123"},
    "receptionist": {
        "username": "e2e_receptionist",
        "password": "E2eRecep!123",
    },
    "manager": {"username": "e2e_manager", "password": "E2eMgr!123"},
}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Desktop viewport so AuthShell brand (md+) and ops Sidebar are visible.
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("E2E_FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def api_url():
    return os.getenv("E2E_API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def guest_credentials():
    return E2E_USERS["guest"]


@pytest.fixture(scope="session")
def receptionist_credentials():
    return E2E_USERS["receptionist"]


@pytest.fixture(scope="session")
def manager_credentials():
    return E2E_USERS["manager"]


@pytest.fixture(scope="session", autouse=True)
def _verify_api_reachable(api_url):
    """Fail fast with a clear message if the stack is not up."""
    try:
        response = requests.post(
            f"{api_url}/api/v1/auth/login/",
            json={},
            timeout=5,
        )
        if response.status_code >= 500:
            pytest.exit(f"API unhealthy at {api_url}: HTTP {response.status_code}", 1)
    except requests.RequestException as exc:
        pytest.exit(
            f"API not reachable at {api_url}. Start stack + seed users "
            f"(make up && docker compose exec django python manage.py seed_e2e_users). "
            f"Error: {exc}",
            1,
        )


def do_login(page, base_url, username, password, *, attempts=5):
    from playwright.sync_api import expect

    last_status = None
    for attempt in range(1, attempts + 1):
        page.goto(f"{base_url}/login")
        page.get_by_label("Username or Email").fill(username)
        # Prefer the password input explicitly (MUI adornment buttons also have "password" labels).
        page.locator('input[type="password"]').fill(password)
        with page.expect_response(
            lambda r: "/auth/login" in r.url and r.request.method == "POST",
            timeout=15000,
        ) as resp_info:
            page.get_by_role("button", name="Sign In").click()
        response = resp_info.value
        last_status = response.status
        if response.ok:
            expect(page).not_to_have_url(f"{base_url}/login", timeout=15000)
            return
        if response.status == 429 and attempt < attempts:
            time.sleep(attempt * 2)
            continue
        break
    raise AssertionError(f"Login failed for {username}: HTTP {last_status}")
