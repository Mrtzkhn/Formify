# Formify - Django User Management API

A Django REST API application for user management with JWT authentication.

## Features

- Custom User model with email-based authentication
- JWT token-based authentication (access & refresh tokens)
- User registration with password validation
- User login/logout functionality
- Token refresh endpoint
- Comprehensive unit tests
- RESTful API endpoints

## Installation

### Prerequisites

- Python 3.10+
- pip

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Formify
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/auth/`

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login user and get JWT tokens |
| POST | `/api/auth/logout/` | Logout user (blacklist refresh token) |
| POST | `/api/auth/token/refresh/` | Refresh access token |

## Usage Examples

### User Registration

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Secret1234",
    "password_confirm": "Secret1234",
    "full_name": "John Doe",
    "phone_number": "+1234567890"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "created_at": "2024-01-01T12:00:00Z",
  "is_active": true
}
```

### User Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Secret1234"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "created_at": "2024-01-01T12:00:00Z",
    "is_active": true
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Token Refresh

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### User Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Response:**
```json
{
  "message": "Successfully logged out."
}
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication:

- **Access Token**: Valid for 5 minutes, used for API requests
- **Refresh Token**: Valid for 7 days, used to get new access tokens

Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Running Tests

```bash
python manage.py test accounts
```

## Project Structure

```
Formify/
├── accounts/                 # User management app
│   ├── models.py            # Custom User model
│   ├── managers.py          # User manager
│   ├── serializers.py       # API serializers
│   ├── views.py             # API views
│   ├── urls.py              # URL routing
│   └── tests.py             # Unit tests
├── config/                  # Django project settings
│   ├── settings.py          # Configuration
│   └── urls.py              # Main URL routing
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Security Features

- Password hashing using Django's built-in password hashers
- JWT token blacklisting for secure logout
- Email normalization for consistency
- Password validation (minimum length, complexity)
- CSRF protection (when using session authentication)
- SQL injection protection through Django ORM

## Configuration

Key settings in `config/settings.py`:

- `AUTH_USER_MODEL = 'accounts.User'` - Custom user model
- `SIMPLE_JWT` - JWT configuration
- `REST_FRAMEWORK` - API framework settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests to ensure everything passes
6. Submit a pull request

## License

This project is licensed under the MIT License.
