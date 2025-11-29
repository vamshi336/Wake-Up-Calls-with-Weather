#!/usr/bin/env python3
"""
Setup script for Vamshi Wake-up Calls application.
This script helps set up the application for local development.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_requirements():
    """Check if required software is installed."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} found")
    
    # Check if pip is available
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        print("✅ pip is available")
    except subprocess.CalledProcessError:
        print("❌ pip is not available")
        return False
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    # Core dependencies that should work on all platforms
    core_deps = [
        "Django==4.2.7",
        "djangorestframework",
        "django-cors-headers",
        "django-environ",
        "celery",
        "redis",
        "twilio",
        "requests",
        "python-decouple",
        "django-phonenumber-field",
        "phonenumbers",
        "django-extensions",
        "gunicorn",
        "dj-database-url",
        "whitenoise",
        "django-celery-beat",
        "django-celery-results",
    ]
    
    for dep in core_deps:
        result = run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}")
        if not result:
            print(f"⚠️  Failed to install {dep}, continuing...")

def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from example...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your configuration")
    else:
        print("ℹ️  .env file already exists or env.example not found")

def setup_database():
    """Set up the database."""
    print("🗄️  Setting up database...")
    
    # Make migrations
    result = run_command(f"{sys.executable} manage.py makemigrations", "Creating migrations")
    if not result:
        return False
    
    # Apply migrations
    result = run_command(f"{sys.executable} manage.py migrate", "Applying migrations")
    if not result:
        return False
    
    return True

def create_superuser():
    """Create a superuser account."""
    print("👤 Creating superuser account...")
    
    # Check if superuser already exists
    check_cmd = f"{sys.executable} manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(is_superuser=True).exists())\""
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0 and "True" in result.stdout:
        print("ℹ️  Superuser already exists")
        return True
    
    # Create superuser
    result = run_command(
        f"{sys.executable} manage.py createsuperuser --username admin --email admin@example.com --noinput",
        "Creating superuser (admin/admin)"
    )
    
    if result:
        print("ℹ️  Superuser created: username=admin, email=admin@example.com")
        print("⚠️  Please set a password using: python manage.py changepassword admin")
    
    return result is not None

def seed_demo_data():
    """Seed the database with demo data."""
    print("🌱 Seeding demo data...")
    
    result = run_command(
        f"{sys.executable} manage.py seed_demo_data --users 8 --calls-per-user 4 --executions 50",
        "Seeding demo data"
    )
    
    return result is not None

def create_logs_directory():
    """Create logs directory."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("ℹ️  Logs directory already exists")

def main():
    """Main setup function."""
    print("🚀 Vamshi Wake-up Calls Setup")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements check failed")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Set up environment
    setup_environment()
    
    # Create logs directory
    create_logs_directory()
    
    # Set up database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Create superuser
    create_superuser()
    
    # Seed demo data
    seed_demo_data()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Twilio and weather API credentials")
    print("2. Start the development server: python manage.py runserver")
    print("3. Visit http://127.0.0.1:8000 to access the application")
    print("4. Visit http://127.0.0.1:8000/admin to access the admin panel")
    print("\nFor Celery (background tasks):")
    print("5. Start Redis server")
    print("6. Start Celery worker: celery -A wakeupcalls_project worker --loglevel=info")
    print("7. Start Celery beat: celery -A wakeupcalls_project beat --loglevel=info")
    print("\nFor Docker:")
    print("8. Run: docker-compose up -d")
    
    print("\n📚 Documentation: README.md")
    print("🐛 Issues: Check the logs/ directory for error logs")

if __name__ == "__main__":
    main()
