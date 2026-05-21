# HMS/tests/e2e/conftest.py
import os

import pytest
import requests


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("E2E_FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def api_url():
    return os.getenv("E2E_API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def admin_token(api_url):
    username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")
    response = requests.post(
        f"{api_url}/api/v1/auth/login/",
        json={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access"]


@pytest.fixture(scope="session")
def api_session(admin_token):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {admin_token}"
    return session


def _create_user(api_session, api_url, username, password, role):
    response = api_session.post(
        f"{api_url}/api/v1/users/",
        json={"username": username, "password": password, "role": role},
        timeout=10,
    )
    if response.status_code not in (200, 201, 409):
        response.raise_for_status()
    return {"username": username, "password": password}


def _delete_user(api_session, api_url, username):
    response = api_session.get(
        f"{api_url}/api/v1/users/",
        params={"username": username},
        timeout=10,
    )
    if response.status_code != 200:
        return
    data = response.json()
    results = data.get("results", data) if isinstance(data, dict) else data
    for user in results:
        if user.get("username") == username:
            api_session.delete(
                f"{api_url}/api/v1/users/{user['id']}/",
                timeout=10,
            )
            break


@pytest.fixture(scope="session")
def guest_credentials(api_session, api_url):
    creds = _create_user(api_session, api_url, "e2e_guest", "E2eGuest!123", "guest")
    yield creds
    _delete_user(api_session, api_url, "e2e_guest")


@pytest.fixture(scope="session")
def receptionist_credentials(api_session, api_url):
    creds = _create_user(
        api_session, api_url, "e2e_receptionist", "E2eRecep!123", "receptionist"
    )
    yield creds
    _delete_user(api_session, api_url, "e2e_receptionist")


@pytest.fixture(scope="session")
def manager_credentials(api_session, api_url):
    creds = _create_user(
        api_session, api_url, "e2e_manager", "E2eMgr!123", "manager"
    )
    yield creds
    _delete_user(api_session, api_url, "e2e_manager")


def do_login(page, base_url, username, password):
    page.goto(f"{base_url}/login")
    page.get_by_label("Username or Email").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign In").click()
