#!/usr/bin/env python
"""Script to create a superuser for Django admin."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')
django.setup()

from accounts.models import User

def create_superuser():
    email = input("Enter email address: ").strip()
    if not email:
        print("[ERROR] Email is required!")
        return
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        print(f"[WARNING] User with email {email} already exists!")
        response = input("Do you want to update it to superuser? (yes/no): ").strip().lower()
        if response != 'yes':
            print("[INFO] Cancelled.")
            return
        user = User.objects.get(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"[SUCCESS] User {email} updated to superuser!")
        return
    
    first_name = input("Enter first name (optional): ").strip()
    last_name = input("Enter last name (optional): ").strip()
    
    password = input("Enter password: ").strip()
    if not password:
        print("[ERROR] Password is required!")
        return
    
    password_confirm = input("Confirm password: ").strip()
    if password != password_confirm:
        print("[ERROR] Passwords do not match!")
        return
    
    # Create superuser
    try:
        user = User.objects.create_user(
            email=email,
            username=email,  # Use email as username
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=True
        )
        print(f"[SUCCESS] Superuser created successfully!")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Staff: {user.is_staff}")
        print(f"Superuser: {user.is_superuser}")
    except Exception as e:
        print(f"[ERROR] Failed to create superuser: {e}")

if __name__ == '__main__':
    print("=== Create Django Superuser ===")
    create_superuser()

