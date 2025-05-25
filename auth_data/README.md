# Authentication Data Storage

This directory stores encrypted TOTP secrets for the authentication service. The secrets are encrypted using Fernet symmetric encryption before being stored in `data.txt`.

## Security Notes

- Secret is encrypted before storage
- Encryption key is stored in environment variables

## Files

- `data.txt`: Encrypted TOTP secret storage
