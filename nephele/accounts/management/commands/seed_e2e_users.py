"""Seed deterministic e2e users for Playwright tests.

Passwords MUST come from the environment (never hardcoded):
  E2E_GUEST_PASSWORD
  E2E_RECEPTIONIST_PASSWORD
  E2E_MANAGER_PASSWORD
"""

import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Guest

USER_SPECS = (
    {
        "username": "e2e_guest",
        "role": "guest",
        "email": "e2e_guest@example.com",
        "first_name": "E2E",
        "last_name": "Guest",
        "password_env": "E2E_GUEST_PASSWORD",
    },
    {
        "username": "e2e_receptionist",
        "role": "receptionist",
        "email": "e2e_receptionist@example.com",
        "first_name": "E2E",
        "last_name": "Reception",
        "password_env": "E2E_RECEPTIONIST_PASSWORD",
    },
    {
        "username": "e2e_manager",
        "role": "manager",
        "email": "e2e_manager@example.com",
        "first_name": "E2E",
        "last_name": "Manager",
        "password_env": "E2E_MANAGER_PASSWORD",
    },
)


class Command(BaseCommand):
    help = "Create/update e2e users; passwords are read from environment variables"

    def handle(self, *args, **options):
        missing = [
            spec["password_env"]
            for spec in USER_SPECS
            if not os.environ.get(spec["password_env"])
        ]
        if missing:
            raise CommandError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        for spec in USER_SPECS:
            password = os.environ[spec["password_env"]]
            group, _ = Group.objects.get_or_create(name=spec["role"])
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "is_active": True,
                },
            )
            user.email = spec["email"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_active = True
            user.set_password(password)
            user.save()
            user.groups.set([group])

            if spec["role"] == "guest":
                Guest.objects.get_or_create(
                    user=user,
                    defaults={
                        "email": spec["email"],
                        "first_name": spec["first_name"],
                        "last_name": spec["last_name"],
                    },
                )

            action = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"e2e user {spec['username']} ({spec['role']}) {action}"
                )
            )
