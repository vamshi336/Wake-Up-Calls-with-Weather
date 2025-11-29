#!/usr/bin/env python
"""Check what data exists in SQLite database."""
import os
import sqlite3

if os.path.exists('db.sqlite3'):
    print("[INFO] SQLite database exists (db.sqlite3)\n")
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables found: {len(tables)}")
        
        # Check users
        try:
            cursor.execute("SELECT COUNT(*) FROM accounts_user")
            user_count = cursor.fetchone()[0]
            print(f"Users in SQLite: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT email, is_staff, is_superuser FROM accounts_user LIMIT 5")
                users = cursor.fetchall()
                print("\nSample users:")
                for email, is_staff, is_superuser in users:
                    print(f"  - {email} (Staff: {is_staff}, Superuser: {is_superuser})")
        except Exception as e:
            print(f"Error checking users: {e}")
        
        # Check wake-up calls
        try:
            cursor.execute("SELECT COUNT(*) FROM wakeup_calls_wakeupcall")
            call_count = cursor.fetchone()[0]
            print(f"\nWake-up calls in SQLite: {call_count}")
        except Exception as e:
            print(f"Error checking wake-up calls: {e}")
        
        # Check executions
        try:
            cursor.execute("SELECT COUNT(*) FROM wakeup_calls_wakeupcallexecution")
            exec_count = cursor.fetchone()[0]
            print(f"Executions in SQLite: {exec_count}")
        except Exception as e:
            print(f"Error checking executions: {e}")
        
        conn.close()
        
        if user_count > 0 or call_count > 0 or exec_count > 0:
            print("\n[INFO] You have data in SQLite that can be migrated to PostgreSQL.")
            print("Would you like to migrate this data? (Next step)")
        else:
            print("\n[INFO] SQLite database is empty. No migration needed.")
            
    except Exception as e:
        print(f"[ERROR] Error reading SQLite database: {e}")
else:
    print("[INFO] No SQLite database found (db.sqlite3 doesn't exist)")
    print("[INFO] Starting fresh with PostgreSQL - no migration needed.")

