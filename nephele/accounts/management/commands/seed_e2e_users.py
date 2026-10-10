"""Seed deterministic users for Playwright e2e tests."""

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.models import Guest

USERS = [
    {
        "username": "e2e_guest",
        "password": "E2eGuest!123",
        "role": "guest",
        "email": "e2e_guest@example.com",
        "first_name": "E2E",
        "last_name": "Guest",
    },
    {
        "username": "e2e_receptionist",
        "password": "E2eRecep!123",
        "role": "receptionist",
        "email": "e2e_receptionist@example.com",
        "first_name": "E2E",
        "last_name": "Reception",
    },
    {
        "username": "e2e_manager",
        "password": "E2eMgr!123",
        "role": "manager",
        "email": "e2e_manager@example.com",
        "first_name": "E2E",
        "last_name": "Manager",
    },
]


class Command(BaseCommand):
    help = "Create/update deterministic e2e users with role groups"

    def handle(self, *args, **options):
        for spec in USERS:
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
            user.set_password(spec["password"])
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
