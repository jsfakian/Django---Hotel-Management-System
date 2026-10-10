# nephele/tests/e2e/conftest.py
import os

import pytest
import requests

# Usernames are public test fixtures; passwords come from the environment only.
E2E_USERNAMES = {
    "guest": "e2e_guest",
    "receptionist": "e2e_receptionist",
    "manager": "e2e_manager",
}

E2E_PASSWORD_ENV = {
    "guest": "E2E_GUEST_PASSWORD",
    "receptionist": "E2E_RECEPTIONIST_PASSWORD",
    "manager": "E2E_MANAGER_PASSWORD",
}


def _credentials(role: str) -> dict:
    env_key = E2E_PASSWORD_ENV[role]
    password = os.environ.get(env_key)
    if not password:
        pytest.exit(
            f"Missing {env_key}. Export e2e passwords before running Playwright tests "
            f"(CI generates them; locally see scripts/ci-local-e2e.sh).",
            returncode=1,
        )
    return {"username": E2E_USERNAMES[role], "password": password}


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
    return _credentials("guest")


@pytest.fixture(scope="session")
def receptionist_credentials():
    return _credentials("receptionist")


@pytest.fixture(scope="session")
def manager_credentials():
    return _credentials("manager")


@pytest.fixture(scope="session", autouse=True)
def _verify_api_reachable(api_url):
    """Fail fast with a clear message if the stack is not up."""
    try:
        response = requests.get(f"{api_url}/api/v1/schema/", timeout=5)
        if response.status_code >= 500:
            pytest.exit(f"API unhealthy at {api_url}: HTTP {response.status_code}", 1)
    except requests.RequestException as exc:
        pytest.exit(
            f"API not reachable at {api_url}. Start stack + seed users "
            f"(make up && bash scripts/ci-local-e2e.sh). Error: {exc}",
            1,
        )


def do_login(page, base_url, username, password):
    page.goto(f"{base_url}/login")
    page.get_by_label("Username or Email").fill(username)
    # Avoid get_by_label("Password") — it also matches the "Show password" icon button.
    page.locator('input[type="password"]').fill(password)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_function(
        "() => !location.pathname.endsWith('/login') || "
        "!!document.querySelector('.MuiAlert-root')",
        timeout=15000,
    )
    alert = page.locator(".MuiAlert-root")
    if alert.count() and alert.first.is_visible():
        raise AssertionError(f"Login failed: {alert.first.inner_text()}")
