"""
Management command to seed demo data for the wake-up calls application.
"""

import random
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from wakeup_calls.models import WakeUpCall, WakeUpCallExecution
from wakeup_calls.tasks import update_next_execution_time
from wakeup_calls.tasks import update_next_execution_time

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for wake-up calls application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of demo users to create'
        )
        parser.add_argument(
            '--calls-per-user',
            type=int,
            default=6,
            help='Number of wake-up calls per user'
        )
        parser.add_argument(
            '--executions',
            type=int,
            default=50,
            help='Number of demo executions to create (minimum 30 required)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing demo data before seeding'
        )
    
    def handle(self, *args, **options):
        # Ensure minimum 30 executions
        if options['executions'] < 30:
            options['executions'] = 30
            self.stdout.write(self.style.WARNING('Minimum 30 executions required. Setting to 30.'))
        
        if options['clear_existing']:
            self.stdout.write('Clearing existing demo data...')
            self.clear_demo_data()
        
        self.stdout.write('Creating comprehensive demo data...')
        
        # Create admin user first
        admin_user = self.create_admin_user()
        self.stdout.write(f'Created admin user: {admin_user.email}')
        
        # Create demo users
        users = self.create_demo_users(options['users'])
        self.stdout.write(f'Created {len(users)} demo users')
        
        # Create wake-up calls
        wakeup_calls = self.create_demo_wakeup_calls(users + [admin_user], options['calls_per_user'])
        self.stdout.write(f'Created {len(wakeup_calls)} demo wake-up calls')
        
        # Create executions (with logging)
        executions = self.create_demo_executions(wakeup_calls, options['executions'])
        self.stdout.write(f'Created {len(executions)} demo executions')
        
        # Create notification logs for demo executions
        notification_logs = self.create_demo_notification_logs(executions)
        self.stdout.write(f'Created {len(notification_logs)} notification logs')
        
        # Create phone verifications
        verifications = self.create_demo_phone_verifications(users)
        self.stdout.write(f'Created {len(verifications)} phone verifications')
        
        # Display summary
        self.display_demo_summary(admin_user, users, wakeup_calls, executions, notification_logs)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded comprehensive demo data!\n'
                f'Summary: {len(users)+1} users, {len(wakeup_calls)} calls, '
                f'{len(executions)} executions, {len(notification_logs)} logs'
            )
        )
    
    def clear_demo_data(self):
        """Clear existing demo data."""
        # Delete demo executions
        WakeUpCallExecution.objects.filter(wakeup_call__is_demo=True).delete()
        
        # Delete demo wake-up calls
        WakeUpCall.objects.filter(is_demo=True).delete()
        
        # Delete demo users (those with email containing 'demo')
        User.objects.filter(email__contains='demo').delete()
    
    def create_demo_users(self, count):
        """Create demo users."""
        users = []
        
        demo_data = [
            {'first_name': 'Alice', 'last_name': 'Johnson', 'zip_code': '10001'},
            {'first_name': 'Bob', 'last_name': 'Smith', 'zip_code': '90210'},
            {'first_name': 'Carol', 'last_name': 'Davis', 'zip_code': '60601'},
            {'first_name': 'David', 'last_name': 'Wilson', 'zip_code': '30301'},
            {'first_name': 'Emma', 'last_name': 'Brown', 'zip_code': '02101'},
            {'first_name': 'Frank', 'last_name': 'Miller', 'zip_code': '98101'},
            {'first_name': 'Grace', 'last_name': 'Taylor', 'zip_code': '33101'},
            {'first_name': 'Henry', 'last_name': 'Anderson', 'zip_code': '80201'},
        ]
        
        for i in range(count):
            user_data = demo_data[i % len(demo_data)]
            
            user = User.objects.create_user(
                username=f"demo_user_{i+1}",
                email=f"demo.user.{i+1}@example.com",
                password="demo123456",
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone_number=f"+1555010{i+1:04d}",
                phone_verified=True,
                zip_code=user_data['zip_code'],
                timezone='America/New_York'
            )
            users.append(user)
        
        return users
    
    def create_demo_wakeup_calls(self, users, calls_per_user):
        """Create demo wake-up calls."""
        wakeup_calls = []
        
        call_names = [
            "Morning Workout", "Work Day", "Weekend Sleep-in", "Early Meeting",
            "Gym Session", "School Day", "Travel Day", "Doctor Appointment",
            "Important Interview", "Weekend Adventure"
        ]
        
        frequencies = ['once', 'daily', 'weekly', 'weekdays', 'weekends', 'custom']
        contact_methods = ['call', 'sms']
        statuses = ['active', 'paused', 'completed']
        
        custom_messages = [
            "Don't forget your morning vitamins!",
            "Today is going to be a great day!",
            "Remember to drink water first thing.",
            "Time to seize the day!",
            "Your future self will thank you for getting up now.",
            "",  # Some calls have no custom message
        ]
        
        for user in users:
            for i in range(calls_per_user):
                # Random time between 5 AM and 10 AM
                hour = random.randint(5, 9)
                minute = random.choice([0, 15, 30, 45])
                scheduled_time = time(hour, minute)
                
                frequency = random.choice(frequencies)
                
                # Set custom frequency days if needed
                days = {
                    'monday': False, 'tuesday': False, 'wednesday': False,
                    'thursday': False, 'friday': False, 'saturday': False, 'sunday': False
                }
                
                if frequency == 'custom':
                    # Randomly select 2-5 days
                    day_names = list(days.keys())
                    selected_days = random.sample(day_names, random.randint(2, 5))
                    for day in selected_days:
                        days[day] = True
                
                wakeup_call = WakeUpCall.objects.create(
                    user=user,
                    name=f"{random.choice(call_names)} {i+1}",
                    phone_number=user.phone_number,
                    contact_method=random.choice(contact_methods),
                    scheduled_time=scheduled_time,
                    frequency=frequency,
                    start_date=date.today() - timedelta(days=random.randint(0, 30)),
                    end_date=None if random.random() > 0.3 else date.today() + timedelta(days=random.randint(30, 90)),
                    include_weather=random.choice([True, False]),
                    weather_zip_code=user.zip_code if random.random() > 0.5 else None,
                    custom_message=random.choice(custom_messages),
                    status=random.choice(statuses),
                    is_demo=True,
                    **days
                )
                
                # Calculate next execution time
                if wakeup_call.status == 'active':
                    update_next_execution_time(wakeup_call)
                
                wakeup_calls.append(wakeup_call)
        
        return wakeup_calls
    
    def create_demo_executions(self, wakeup_calls, count):
        """Create demo executions."""
        executions = []
        
        statuses = ['completed', 'failed', 'pending', 'in_progress']
        twilio_statuses = ['completed', 'busy', 'no-answer', 'failed', 'canceled']
        user_responses = ['1', '2', '', 'reschedule', 'snooze']
        
        error_messages = [
            "Phone number not reachable",
            "Call rejected by recipient",
            "Network timeout",
            "Invalid phone number",
            "",  # No error for successful calls
        ]
        
        # Sample weather data
        sample_weather = {
            "main": {"temp": 72, "humidity": 65},
            "weather": [{"description": "partly cloudy"}],
            "name": "New York"
        }
        
        for i in range(count):
            wakeup_call = random.choice(wakeup_calls)
            
            # Random execution time in the past 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            scheduled_for = timezone.now() - timedelta(
                days=days_ago, hours=hours_ago, minutes=minutes_ago
            )
            
            status = random.choice(statuses)
            
            execution = WakeUpCallExecution.objects.create(
                wakeup_call=wakeup_call,
                scheduled_for=scheduled_for,
                executed_at=scheduled_for + timedelta(seconds=random.randint(1, 300)),
                status=status,
                twilio_sid=f"demo_call_{i+1}_{random.randint(1000, 9999)}",
                twilio_status=random.choice(twilio_statuses) if status != 'pending' else None,
                weather_data=sample_weather if wakeup_call.include_weather and random.random() > 0.3 else None,
                error_message=random.choice(error_messages) if status == 'failed' else None,
                user_response=random.choice(user_responses) if wakeup_call.contact_method == 'call' and random.random() > 0.5 else None,
                interaction_data={'demo': True, 'call_duration': random.randint(30, 180)} if random.random() > 0.7 else None
            )
            
            executions.append(execution)
        
        return executions
    
    def create_admin_user(self):
        """Create or get admin user."""
        try:
            admin_user = User.objects.get(email='admin@Vamshi.com')
            self.stdout.write('Admin user already exists')
        except User.DoesNotExist:
            # Check if username 'admin' exists and use a different one if needed
            username = 'admin'
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'admin_{counter}'
                counter += 1
            
            admin_user = User.objects.create_user(
                username=username,
                email='admin@Vamshi.com',
                password='admin123456',
                first_name='Admin',
                last_name='User',
                phone_number='+15550100000',
                phone_verified=True,
                zip_code='10001',
                timezone='America/New_York',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
        
        return admin_user
    
    def create_demo_notification_logs(self, executions):
        """Create notification logs for demo executions to show logging capability."""
        from notifications.models import NotificationLog
        
        logs = []
        
        for execution in executions:
            if execution.status in ['completed', 'failed']:
                # Create SMS log
                if execution.wakeup_call.contact_method == 'sms' or execution.status == 'failed':
                    log = NotificationLog.objects.create(
                        user=execution.wakeup_call.user,
                        notification_type='sms',
                        recipient_phone=str(execution.wakeup_call.phone_number),
                        message_content=self.generate_demo_message(execution),
                        status='sent' if execution.status == 'completed' else 'failed',
                        twilio_sid=execution.twilio_sid,
                        twilio_status=execution.twilio_status,
                        is_demo=True,
                        sent_at=execution.executed_at,
                        delivered_at=execution.executed_at + timezone.timedelta(seconds=random.randint(1, 30)) if execution.status == 'completed' else None,
                        twilio_error_message=execution.error_message if execution.status == 'failed' else None
                    )
                    logs.append(log)
                
                # Create call log for voice calls
                if execution.wakeup_call.contact_method == 'call' and execution.status == 'completed':
                    call_log = NotificationLog.objects.create(
                        user=execution.wakeup_call.user,
                        notification_type='voice',
                        recipient_phone=str(execution.wakeup_call.phone_number),
                        message_content=f"Voice call: {execution.wakeup_call.name}",
                        status='completed',
                        twilio_sid=f"voice_{execution.twilio_sid}",
                        twilio_status='completed',
                        is_demo=True,
                        sent_at=execution.executed_at,
                        delivered_at=execution.executed_at + timezone.timedelta(seconds=random.randint(5, 60)),
                        metadata={'call_duration': random.randint(30, 180), 'user_response': execution.user_response}
                    )
                    logs.append(call_log)
        
        return logs
    
    def create_demo_phone_verifications(self, users):
        """Create phone verification records for demo users."""
        from accounts.models import PhoneVerification
        
        verifications = []
        
        for user in users:
            verification = PhoneVerification.objects.create(
                user=user,
                phone_number=user.phone_number,
                verification_code=f"{random.randint(100000, 999999)}",
                is_verified=True,
                attempts=1,
                expires_at=timezone.now() + timezone.timedelta(hours=1)
            )
            verifications.append(verification)
        
        return verifications
    
    def generate_demo_message(self, execution):
        """Generate realistic demo message content."""
        wakeup_call = execution.wakeup_call
        
        greeting = "🧪 DEMO: Good morning! This is your wake-up call from Vamshi."
        
        weather_msg = ""
        if wakeup_call.include_weather and execution.weather_data:
            temp = execution.weather_data.get('main', {}).get('temp', 70)
            desc = execution.weather_data.get('weather', [{}])[0].get('description', 'clear')
            weather_msg = f" The weather is {desc} with a temperature of {temp}°F."
        
        custom_msg = f" {wakeup_call.custom_message}" if wakeup_call.custom_message else ""
        
        return f"{greeting}{weather_msg}{custom_msg}".strip()
    
    def display_demo_summary(self, admin_user, users, wakeup_calls, executions, logs):
        """Display comprehensive summary of created demo data."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DEMO DATA SUMMARY'))
        self.stdout.write('='*60)
        
        # Admin user info
        self.stdout.write(f'ADMIN USER: {admin_user.email} (password: admin123456)')
        self.stdout.write(f'   Role: {admin_user.role} | Staff: {admin_user.is_staff} | Superuser: {admin_user.is_superuser}')
        
        # Regular users
        self.stdout.write(f'\nDEMO USERS ({len(users)}):')
        for user in users[:3]:  # Show first 3
            self.stdout.write(f'   - {user.email} (password: demo123456)')
        if len(users) > 3:
            self.stdout.write(f'   ... and {len(users)-3} more')
        
        # Wake-up calls breakdown
        active_calls = sum(1 for call in wakeup_calls if call.status == 'active')
        demo_calls = sum(1 for call in wakeup_calls if call.is_demo)
        self.stdout.write(f'\nWAKE-UP CALLS ({len(wakeup_calls)}):')
        self.stdout.write(f'   - Active: {active_calls}')
        self.stdout.write(f'   - Demo mode: {demo_calls}')
        self.stdout.write(f'   - With weather: {sum(1 for call in wakeup_calls if call.include_weather)}')
        
        # Executions breakdown
        completed = sum(1 for ex in executions if ex.status == 'completed')
        failed = sum(1 for ex in executions if ex.status == 'failed')
        self.stdout.write(f'\nEXECUTIONS ({len(executions)}):')
        self.stdout.write(f'   - Completed: {completed}')
        self.stdout.write(f'   - Failed: {failed}')
        self.stdout.write(f'   - With weather data: {sum(1 for ex in executions if ex.weather_data)}')
        
        # Notification logs
        sms_logs = sum(1 for log in logs if log.notification_type == 'sms')
        voice_logs = sum(1 for log in logs if log.notification_type == 'voice')
        self.stdout.write(f'\nNOTIFICATION LOGS ({len(logs)}):')
        self.stdout.write(f'   - SMS logs: {sms_logs}')
        self.stdout.write(f'   - Voice logs: {voice_logs}')
        self.stdout.write(f'   - All suppressed (demo mode): {sum(1 for log in logs if log.is_demo)}')
        
        # Access information
        self.stdout.write(f'\nACCESS INFORMATION:')
        self.stdout.write(f'   - Web Interface: http://127.0.0.1:8000/')
        self.stdout.write(f'   - Admin Panel: http://127.0.0.1:8000/admin/')
        self.stdout.write(f'   - API Documentation: http://127.0.0.1:8000/api/')
        self.stdout.write(f'   - Monitor Dashboard: http://127.0.0.1:8000/monitor/')
        
        self.stdout.write('\n' + '='*60)
