# 🚀 Production Deployment Guide

## Prerequisites

### 1. Verify Phone Numbers in Twilio
**CRITICAL FIRST STEP:**
1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
2. Add these numbers:
   - `+919491151188`
   - `+917036702018` 
   - Any other test numbers
3. Verify each number via SMS/Voice

### 2. Environment Variables
Create a `.env.prod` file with:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=your-domain.com,*.amazonaws.com

# Database (use AWS RDS or similar)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis (use AWS ElastiCache or similar)
REDIS_URL=redis://your-redis-host:6379/0

# Twilio (REAL CREDENTIALS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number

# Weather API
WEATHER_API_KEY=49efc329e9d6409fad471128252911

# AWS (for CloudWatch logging)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_CLOUDWATCH_LOG_GROUP=/aws/ecs/wakeupcalls

# Production Settings
DEMO_MODE=False
PHONE_VERIFICATION_BYPASS=False
```

## Deployment Options

### Option 1: AWS Fargate (Recommended)
```bash
# 1. Configure AWS CLI
aws configure

# 2. Run deployment script
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Docker Compose (Simple)
```bash
# 1. Build and run
docker-compose -f docker-compose.prod.yml up -d

# 2. Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 3. Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Option 3: Heroku (Quick Deploy)
```bash
# 1. Install Heroku CLI
# 2. Create app
heroku create your-wakeupcalls-app

# 3. Add environment variables
heroku config:set DEBUG=False
heroku config:set TWILIO_ACCOUNT_SID=your_sid
# ... add all other env vars

# 4. Deploy
git push heroku main
```

## Testing Voice Calls

### Why Voice Calls Need Real Deployment:
1. **Twilio Webhooks**: Need public URL for TwiML
2. **DTMF Support**: Requires real phone interaction
3. **Voice Commands**: Need actual voice processing

### Test Checklist:
- [ ] Phone numbers verified in Twilio
- [ ] App deployed with public URL
- [ ] Webhook URLs configured
- [ ] Voice call test successful
- [ ] SMS fallback working
- [ ] DTMF commands working (1=snooze, 2=cancel)

## Voice Call Flow:
1. **Celery triggers call**
2. **Twilio makes voice call**
3. **User answers phone**
4. **TwiML plays message + weather**
5. **User can press 1 (snooze) or 2 (cancel)**
6. **Webhook updates call status**

## Post-Deployment:
1. **Test wake-up calls** with verified numbers
2. **Monitor CloudWatch logs**
3. **Check Celery worker status**
4. **Verify webhook endpoints**
5. **Test admin functions**

## Production Checklist:
- [ ] Twilio account upgraded (if needed)
- [ ] Phone numbers verified
- [ ] Environment variables set
- [ ] Database configured
- [ ] Redis configured
- [ ] AWS resources created
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Monitoring setup
- [ ] Backup strategy implemented

Ready for production deployment! 🎉
