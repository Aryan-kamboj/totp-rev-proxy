# Two-Factor Authentication System

This project implements a simple plug and play two-factor authentication (2FA) system over any web hosted application using [Caddy](https://caddyserver.com/) as reverse proxy and [FastAPI](https://fastapi.tiangolo.com/) as authentication service using TOTP (Time-based One-Time Password).

## Features

- TOTP-based two-factor authentication
- JWT-based session management
- Encrypted TOTP secret storage
- Reset functionality for TOTP secret

## Project Structure

```
two_factor_rev_proxy/
├── auth_app/         # FastAPI authentication service
├── auth_data/        # Encrypted TOTP secret storage
├── main_app/         # Just a simple fastapi application playing the role of protected application 
├── caddy_config/     # Caddy configuration files not being used here 
└── caddy_data/       # Caddy runtime data not being used here
```

## Setup

1. Configure environment variables:
Create a `.env` file with the following variables:
```
JWT_SECRET=your_jwt_secret_key
ENCRYPTION_KEY=your_encryption_key
PROTECTED_APP_NAME=your_app_name
TOTP_SECRET_RESET_PASSWORD=your_reset_password
```
2. Run the authentication service:
```bash
docker compose up --build
```

## Usage

1. Access the protected application through your browser 
2. If not authenticated, you'll be redirected to the OTP form
3. Enter your 6-digit OTP from your authenticator app
4. After successful authentication, you'll be redirected to the protected application

## Security Notes

- JWT tokens are valid for 5 hours
- All cookies are marked as secure and HTTP-only
- TOTP secrets are encrypted before storage
- Environment variables should be kept secure

## License

MIT License
