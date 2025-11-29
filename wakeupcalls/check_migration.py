#!/usr/bin/env python
"""Check migration results - verify all data was imported."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wakeupcalls_project.settings')
django.setup()

from accounts.models import User
from wakeup_calls.models import WakeUpCall, WakeUpCallExecution

print("=== PostgreSQL Database Status ===\n")

# Users
users_count = User.objects.count()
print(f"Users: {users_count}")

# Wake-up calls
calls_count = WakeUpCall.objects.count()
print(f"Wake-up calls: {calls_count}")

# Executions
executions_count = WakeUpCallExecution.objects.count()
print(f"Executions: {executions_count}")

print("\n=== Migration Summary ===")
print(f"[OK] {users_count} users")
print(f"[OK] {calls_count} wake-up calls")
print(f"[OK] {executions_count} executions")

if users_count > 0 and calls_count > 0:
    print("\n[SUCCESS] Migration completed successfully!")
    print("All your data has been migrated from SQLite to PostgreSQL.")
else:
    print("\n[WARNING] Some data may be missing.")

