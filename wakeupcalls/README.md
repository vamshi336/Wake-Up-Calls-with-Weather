# Vamshi Wake-up Calls

A comprehensive Django application that provides personalized wake-up calls with weather updates via Twilio. Users can schedule wake-up calls delivered through phone calls or SMS messages, complete with current weather information for their location.

## Features

### Core Functionality
- **Multiple Contact Methods**: Choose between voice calls or SMS messages
- **Weather Integration**: Get current weather conditions with your wake-up call
- **Flexible Scheduling**: Daily, weekly, weekdays-only, weekends-only, or custom schedules
- **Interactive Voice Calls**: Use voice commands or DTMF to snooze, reschedule, or cancel
- **Phone Verification**: Secure phone number verification system
- **Demo Mode**: Safe testing without actual calls/messages

### User Management
- **User Roles**: Regular users and admin roles
- **Profile Management**: Update personal information and preferences
- **Phone Verification**: SMS-based phone number verification
- **Timezone Support**: Proper timezone handling for scheduling

### API & Integration
- **REST API**: Complete API for external integrations
- **Webhook Support**: Twilio webhook integration for delivery status
- **External Scheduling**: API endpoints for third-party integrations
- **Inbound Call Support**: (Optional) Schedule via phone calls

### Infrastructure
- **Containerized**: Docker and Docker Compose support
- **AWS Ready**: Fargate deployment configuration
- **Scalable**: Celery for background tasks and scheduling
- **Monitoring**: CloudWatch logging integration
- **Queue System**: Redis-based task queue

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Redis (for Celery)
- PostgreSQL (optional, SQLite works for development)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd wakeupcalls
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create a superuser**
```bash
python manage.py createsuperuser
```

6. **Seed demo data**
```bash
python manage.py seed_demo_data --users 5 --calls-per-user 3 --executions 20
```

7. **Start the development server**
```bash
python manage.py runserver
```

8. **Start Celery (in separate terminals)**
```bash
# Worker
celery -A wakeupcalls_project worker --loglevel=info

# Beat scheduler
celery -A wakeupcalls_project beat --loglevel=info
```

### Using Docker

1. **Start all services**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f web
```

3. **Access the application**
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/api/
- Admin Panel: http://localhost:8000/admin/

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Weather API
OPENWEATHER_API_KEY=your_openweather_api_key

# Redis/Celery
REDIS_URL=redis://localhost:6379/0

# Demo Mode (prevents actual calls/SMS)
DEMO_MODE=True
```

### Required External Services

1. **Twilio Account**
   - Sign up at https://www.twilio.com/
   - Get Account SID, Auth Token, and Phone Number
   - Configure webhook URLs for delivery status

2. **OpenWeatherMap API**
   - Sign up at https://openweathermap.org/api
   - Get free API key for weather data

3. **Redis Server**
   - Install locally or use cloud service
   - Required for Celery task queue

## API Documentation

### Authentication
The API uses Token Authentication. Include the token in the Authorization header:
```
Authorization: Token your-token-here
```

### Key Endpoints

#### User Management
- `POST /api/accounts/register/` - User registration
- `POST /api/accounts/login/` - User login
- `GET /api/accounts/profile/` - Get user profile
- `POST /api/accounts/verify-phone/request/` - Request phone verification

#### Wake-up Calls
- `GET /api/wakeup-calls/` - List wake-up calls
- `POST /api/wakeup-calls/` - Create wake-up call
- `GET /api/wakeup-calls/{id}/` - Get wake-up call details
- `PUT /api/wakeup-calls/{id}/` - Update wake-up call
- `POST /api/wakeup-calls/{id}/status/` - Update status

#### Notifications
- `GET /api/notifications/logs/` - Get notification history
- `GET /api/notifications/stats/` - Get notification statistics

### Example API Usage

**Create a wake-up call:**
```bash
curl -X POST http://localhost:8000/api/wakeup-calls/ \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Workout",
    "phone_number": "+1234567890",
    "contact_method": "call",
    "scheduled_time": "07:00:00",
    "frequency": "weekdays",
    "include_weather": true,
    "custom_message": "Time for your workout!"
  }'
```

## Deployment

### AWS Fargate Deployment

1. **Prerequisites**
   - AWS CLI configured
   - Docker installed
   - ECS cluster created
   - RDS PostgreSQL instance
   - ElastiCache Redis cluster
   - Secrets Manager for sensitive data

2. **Deploy using the script**
```bash
./deploy.sh
```

3. **Manual deployment steps**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t wakeupcalls-app .
docker tag wakeupcalls-app:latest <account>.dkr.ecr.us-east-1.amazonaws.com/wakeupcalls-app:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/wakeupcalls-app:latest

# Update ECS service
aws ecs update-service --cluster wakeupcalls-cluster --service wakeupcalls-service --force-new-deployment
```

### Production Configuration

1. **Environment Variables**
   - Set `DEBUG=False`
   - Set `DEMO_MODE=False`
   - Use strong `SECRET_KEY`
   - Configure production database
   - Set up CloudWatch logging

2. **Security**
   - Use AWS Secrets Manager for sensitive data
   - Configure VPC and security groups
   - Set up SSL/TLS certificates
   - Enable WAF protection

## Architecture

### Components
- **Django Web Application**: Main application server
- **Celery Workers**: Background task processing
- **Celery Beat**: Periodic task scheduling
- **Redis**: Message broker and cache
- **PostgreSQL**: Primary database
- **Twilio**: SMS and voice call service
- **OpenWeatherMap**: Weather data API

### Data Flow
1. User schedules wake-up call via web interface or API
2. Celery Beat triggers wake-up call processing every minute
3. Celery Worker executes wake-up calls
4. Weather service fetches current conditions
5. Twilio service makes call or sends SMS
6. Webhook receives delivery status updates
7. User can interact with voice calls (snooze, cancel, etc.)

## Development

### Project Structure
```
wakeupcalls/
├── accounts/           # User management and authentication
├── wakeup_calls/      # Wake-up call models and logic
├── notifications/     # Twilio integration and logging
├── weather/           # Weather API integration
├── web/              # Web interface views and templates
├── templates/        # HTML templates
├── wakeupcalls_project/  # Django project settings
├── requirements.txt  # Python dependencies
├── Dockerfile       # Container configuration
├── docker-compose.yml  # Local development setup
└── README.md        # This file
```

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Linting
flake8 .

# Type checking
mypy .

# Security checks
bandit -r .
```

## Monitoring and Logging

### CloudWatch Integration
- Application logs sent to CloudWatch
- Custom metrics for wake-up call success rates
- Alarms for failed executions

### Health Checks
- Docker health checks
- ECS health checks
- API health endpoint: `/api/`

### Metrics
- Wake-up call success/failure rates
- API response times
- Celery task processing times
- Twilio delivery rates

## Troubleshooting

### Common Issues

1. **Celery tasks not executing**
   - Check Redis connection
   - Verify Celery worker is running
   - Check task queue in Redis

2. **Twilio calls failing**
   - Verify Twilio credentials
   - Check phone number format
   - Ensure webhook URLs are accessible

3. **Weather data not loading**
   - Verify OpenWeatherMap API key
   - Check API rate limits
   - Verify zip code format

### Logs
```bash
# Django logs
tail -f logs/django.log

# Docker logs
docker-compose logs -f web

# Celery logs
docker-compose logs -f celery
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints at `/api/`

---

**Vamshi Wake-up Calls** - Never oversleep again! 🌅📞
