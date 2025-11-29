# Vamshi Wake-up Calls - Setup Guide

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
python setup.py
```

### Option 2: Manual Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp env.example .env
# Edit .env with your configuration
```

3. **Set up Database**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create Superuser**
```bash
python manage.py createsuperuser
```

5. **Seed Demo Data**
```bash
python manage.py seed_demo_data --users 5 --calls-per-user 3 --executions 20
```

6. **Start Development Server**
```bash
python manage.py runserver
```

### Option 3: Docker Setup
```bash
docker-compose up -d
```

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file with the following:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Twilio Configuration (Required for calls/SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Weather API (Required for weather updates)
OPENWEATHER_API_KEY=your_openweather_api_key

# Demo Mode (Set to False for production)
DEMO_MODE=True
```

### Getting API Keys

1. **Twilio Account**
   - Sign up at https://www.twilio.com/
   - Get Account SID, Auth Token, and Phone Number from Console
   - Add webhook URL: `http://your-domain.com/api/notifications/webhook/twilio/`

2. **OpenWeatherMap API**
   - Sign up at https://openweathermap.org/api
   - Get free API key (5-day forecast, current weather)

## 🌐 Access Points

After setup, access the application at:

- **Web Interface**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/api/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### Demo Accounts

The setup creates demo users:
- **Admin**: username=`admin`, email=`admin@example.com`
- **Demo Users**: `demo.user.1@example.com` to `demo.user.5@example.com` (password: `demo123456`)

## 📱 Features Overview

### Core Features
- ✅ **Voice & SMS Wake-up Calls**: Choose between phone calls or text messages
- ✅ **Weather Integration**: Current weather conditions included in calls
- ✅ **Flexible Scheduling**: Daily, weekly, weekdays, weekends, or custom schedules
- ✅ **Interactive Voice Calls**: Voice commands and DTMF for snooze/cancel/reschedule
- ✅ **Phone Verification**: SMS-based phone number verification
- ✅ **Demo Mode**: Safe testing without actual calls/messages

### User Management
- ✅ **User Registration & Login**: Web-based account creation
- ✅ **Profile Management**: Update personal information and preferences
- ✅ **Role-based Access**: User and admin roles
- ✅ **Phone Verification**: Secure phone number ownership verification

### API & Integration
- ✅ **REST API**: Complete API for external integrations
- ✅ **Token Authentication**: Secure API access
- ✅ **Webhook Support**: Twilio delivery status updates
- ✅ **External Scheduling**: API endpoints for third-party systems

### Infrastructure
- ✅ **Containerized**: Docker and Docker Compose support
- ✅ **AWS Ready**: Fargate deployment configuration
- ✅ **Background Tasks**: Celery for wake-up call processing
- ✅ **Monitoring**: Comprehensive logging and error tracking
- ✅ **Scalable**: Redis-based task queue

## 🔄 Background Services

For full functionality, you need these services running:

### Redis (Required for Celery)
```bash
# Install Redis
# Windows: Download from https://redis.io/download
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server
```

### Celery Worker (Processes wake-up calls)
```bash
celery -A wakeupcalls_project worker --loglevel=info
```

### Celery Beat (Schedules wake-up calls)
```bash
celery -A wakeupcalls_project beat --loglevel=info
```

## 🧪 Testing the Application

### 1. Web Interface Testing
1. Visit http://127.0.0.1:8000
2. Register a new account or login with demo account
3. Create a wake-up call with demo mode enabled
4. Check the dashboard for statistics

### 2. API Testing
```bash
# Register a user
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# Login and get token
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Create wake-up call (use token from login)
curl -X POST http://127.0.0.1:8000/api/wakeup-calls/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Workout",
    "phone_number": "+1234567890",
    "contact_method": "sms",
    "scheduled_time": "07:00:00",
    "frequency": "daily",
    "include_weather": true
  }'
```

### 3. Admin Panel Testing
1. Visit http://127.0.0.1:8000/admin/
2. Login with admin credentials
3. Explore wake-up calls, users, and notification logs

## 🚀 Production Deployment

### AWS Fargate Deployment

1. **Prerequisites**
   - AWS CLI configured
   - Docker installed
   - ECS cluster created
   - RDS PostgreSQL instance
   - ElastiCache Redis cluster

2. **Deploy**
```bash
./deploy.sh
```

### Environment Variables for Production
```bash
DEBUG=False
DEMO_MODE=False
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://your-redis-cluster:6379/0
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## 🔍 Troubleshooting

### Common Issues

1. **"Twilio credentials not configured" warning**
   - This is normal in demo mode
   - Add Twilio credentials to .env file for actual calls

2. **Celery tasks not executing**
   - Ensure Redis is running
   - Start Celery worker and beat processes
   - Check Redis connection in settings

3. **Weather data not loading**
   - Add OpenWeatherMap API key to .env
   - Check API rate limits (60 calls/minute for free tier)

4. **Phone verification not working**
   - Ensure Twilio credentials are correct
   - Check phone number format (+1234567890)
   - Verify webhook URL is accessible

### Logs and Debugging

- **Django logs**: `logs/django.log`
- **Console output**: Check terminal where server is running
- **Admin panel**: View notification logs and execution history
- **API health check**: http://127.0.0.1:8000/api/

## 📚 Additional Resources

- **API Documentation**: Available at `/api/` endpoint
- **Django Admin**: Full admin interface for data management
- **Demo Data**: Pre-populated with sample wake-up calls and executions
- **Docker Support**: Full containerization with docker-compose
- **AWS Deployment**: Ready-to-use Fargate configuration

## 🆘 Support

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Verify all environment variables are set correctly
3. Ensure all required services (Redis) are running
4. Check the API health endpoint: `/api/`
5. Review the Django admin panel for data integrity

---

**Happy wake-up calling! 🌅📞**
