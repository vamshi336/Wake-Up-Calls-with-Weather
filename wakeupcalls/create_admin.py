#!/usr/bin/env python
"""Create admin superuser - non-interactive version."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')
django.setup()

from accounts.models import User

def create_admin(email='vamshi@gmail.com', password='Vamshi@123$', first_name='Vamshi', last_name='Admin'):
    """Create or update an admin superuser."""
    
    # Check if user already exists
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if not created:
        # User exists - update to superuser
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.username = email  # Ensure username matches email
        print(f"[INFO] User {email} already exists. Updating to superuser...")
    else:
        print(f"[INFO] Creating new superuser: {email}")
    
    # Set password
    user.set_password(password)
    user.save()
    
    print(f"[SUCCESS] Superuser configured successfully!")
    print(f"  Email: {user.email}")
    print(f"  Username: {user.username}")
    print(f"  Staff: {user.is_staff}")
    print(f"  Superuser: {user.is_superuser}")
    print(f"  Active: {user.is_active}")
    print(f"\nYou can now login at: http://localhost:8000/admin/")

if __name__ == '__main__':
    # Allow command-line arguments
    if len(sys.argv) > 1:
        email = sys.argv[1] if len(sys.argv) > 1 else 'vamshi@gmail.com'
        password = sys.argv[2] if len(sys.argv) > 2 else 'Vamshi@123$'
        first_name = sys.argv[3] if len(sys.argv) > 3 else 'Vamshi'
        last_name = sys.argv[4] if len(sys.argv) > 4 else 'Admin'
        create_admin(email, password, first_name, last_name)
    else:
        # Use defaults
        print("=== Creating Admin Superuser (Default) ===")
        print("Email: vamshi@gmail.com")
        print("Password: Vamshi@123$")
        print("\nTo customize, run: python create_admin.py <email> <password> <first_name> <last_name>")
        print("\nCreating admin user...\n")
        create_admin()

