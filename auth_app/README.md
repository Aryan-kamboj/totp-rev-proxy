# Authentication Service

This directory contains the FastAPI-based authentication service that handles:

- TOTP (Time-based One-Time Password) generation and verification
- JWT token management
- Session handling
- User interface for OTP entry

## Files

- `main.py`: Main FastAPI application with all endpoints
- `templates/`: HTML templates for the OTP interface
- `requirements.txt`: Python dependencies

## Endpoints

- `/verify`: JWT token verification endpoint
- `/otp`: OTP form and submission endpoint
- `/reset-totp-secret`: Endpoint for resetting TOTP secret

## Security Features

- All cookies are marked as secure and HTTP-only
- JWT tokens with expiration
- Encrypted TOTP secret storage
- Input validation and sanitization
- Rate limiting (TODO)

## Development

To run the service independently (not recommended):
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Environment Variables

- `JWT_SECRET`: Secret key for JWT signing
- `ENCRYPTION_KEY`: Key for encrypting TOTP secrets
- `PROTECTED_APP_NAME`: Name of the protected application
- `TOTP_SECRET_RESET_PASSWORD`: Password for resetting TOTP secret
