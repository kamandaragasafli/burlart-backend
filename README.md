# Burlart Backend

Django REST Framework backend for Burlart platform.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file:
```bash
cp .env.example .env
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/logout/` - Logout user
- `GET /api/auth/profile/` - Get user profile (authenticated)
- `PUT/PATCH /api/auth/profile/update/` - Update user profile (authenticated)
- `POST /api/auth/token/refresh/` - Refresh JWT token

## Example Requests

### Register
```json
POST /api/auth/register/
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "password2": "password123",
  "language": "en",
  "theme": "dark"
}
```

### Login
```json
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "password123"
}
```

