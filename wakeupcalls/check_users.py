#!/usr/bin/env python
"""Check existing users in the database."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')
django.setup()

from accounts.models import User

print("=== Current Users in PostgreSQL Database ===\n")
users = User.objects.all()

if users.exists():
    print(f"Total users: {users.count()}\n")
    for user in users:
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Name: {user.first_name} {user.last_name}")
        print(f"Staff: {user.is_staff}")
        print(f"Superuser: {user.is_superuser}")
        print(f"Active: {user.is_active}")
        print("-" * 50)
else:
    print("No users found in database.")
    print("\nYou'll need to create users or migrate from SQLite.")

