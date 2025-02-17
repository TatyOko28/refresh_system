## Launch Docker Services

```bash
docker-compose up -d
```

To stop Docker services:
```bash
docker-compose down
```

To rebuild and restart services:
```bash
docker-compose up --build
```

## Run Tests

Run all tests
```bash
docker-compose -f docker-compose.test.yml up --build   //bizzard
```

Run all tests for the authentication app:
```bash
docker-compose exec web pytest apps/authentication/tests/ -v //bizzard
```

Run specific test files:
```bash
docker-compose exec web pytest apps/referrals/tests/test_service.py -v
```

To run tests in the background with Docker:
```bash
docker-compose up -d --build
```

---


# Referral System API

A Django-based RESTful API service for managing referral systems with JWT authentication, async operations, and third-party integrations.

## Features

- User authentication with JWT and OAuth 2.0
- Referral code management
- Email verification with Email Hunter
- User data enrichment with Clearbit
- Redis caching for improved performance
- Comprehensive API documentation
- Asynchronous operations
- PostgreSQL database

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 13+
- Redis 6+

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/referral-system.git
cd referral-system
```

2. Create a `.env` file:
```bash
cp .env.example .env
```

3. Build and start services:
```bash
docker-compose up --build
```

4. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

5. Access the API:
- API: http://localhost:8000/api/v1/
- Documentation: http://localhost:8000/swagger/

## API Documentation

### Authentication

#### Register User
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password"
}
```

### Referral Management

#### Create Referral Code
```http
POST /api/v1/referrals/codes/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "expires_at": "2024-12-31T23:59:59Z"
}
```

#### Register with Referral Code
```http
POST /api/v1/referrals/register/
Content-Type: application/json

{
    "referral_code": "CODE123",
    "email": "newuser@example.com",
    "password": "secure_password"
}
```

## Development

### Running Tests
```bash
docker-compose exec web pytest  //bizard
```

Run a specific test file:
```bash
docker-compose exec web pytest apps/referrals/tests/test_views.py    
```





## Deployment

### Production Setup
1. Update environment variables:
   - `DEBUG=0`
   - Secure `SECRET_KEY`
   - Database credentials
   - API keys for Clearbit and Email Hunter

2. Build and deploy:
```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Security Considerations
- Use HTTPS in production
- Regularly rotate JWT secrets
- Monitor API rate limits
- Keep dependencies updated
- Regular security audits

## Third-Party Integrations

### Clearbit
Used for enriching user data during registration.
Configured via:
- `CLEARBIT_API_KEY` in .env

### Email Hunter
Verifies email addresses during registration.
Configured via:
- `EMAILHUNTER_API_KEY` in .env

## Caching

Redis is used for caching:
- Referral codes
- Enriched user data
- API responses

Configure cache settings in `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
    }
}
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request




