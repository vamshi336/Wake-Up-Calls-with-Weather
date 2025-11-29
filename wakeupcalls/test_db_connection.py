#!/usr/bin/env python
"""Quick script to test PostgreSQL database connection."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')
django.setup()

from django.db import connection

try:
    connection.ensure_connection()
    print("[SUCCESS] PostgreSQL connection successful!")
    print(f"Database: {connection.settings_dict['NAME']}")
    print(f"Host: {connection.settings_dict['HOST']}")
    print(f"User: {connection.settings_dict['USER']}")
    print(f"Port: {connection.settings_dict['PORT']}")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    exit(1)

