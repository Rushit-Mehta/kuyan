# Security Policy

## Overview

KUYAN is a privacy-focused, local-only financial tracking application. Security and privacy are core principles of this project.

## Data Privacy

### Local-Only Storage
- All financial data is stored **locally** in SQLite database files
- **No cloud synchronization** or external data transmission (except currency exchange rates)
- **No telemetry** or analytics collection
- **No third-party tracking**

### What Data Leaves Your Machine?
KUYAN only makes external requests to:
- **frankfurter.app** - Free currency exchange rate API (no authentication required)
- No other external services are contacted

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

We support the latest stable release. Security updates will be provided for the current major version.

## Reporting a Vulnerability

If you discover a security vulnerability in KUYAN, please report it responsibly:

### DO NOT
- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it's fixed

### DO
1. **Create a GitHub Security Advisory**
   - Go to the "Security" tab in the repository
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

2. **Or contact privately**
   - Email the maintainer (check GitHub profile for contact)
   - Include detailed steps to reproduce
   - Allow time for a fix before public disclosure

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

## Security Best Practices for Users

### Database Security
- Keep your `kuyan.db` file secure
- Set appropriate file permissions (read/write for owner only)
  ```bash
  chmod 600 kuyan.db
  ```
- Don't share your database file publicly
- Use encrypted backups when storing in cloud services

### Backup Security
- Encrypt backups before uploading to cloud storage
- Use strong passwords for encrypted archives
- Store backups in multiple secure locations
- Regularly test backup restoration

### Docker Security
- Keep Docker Desktop updated
- Use named volumes for data persistence
- Don't expose port 8501 to the internet
- Review container permissions

### System Security
- Keep your operating system updated
- Use strong passwords/encryption for your computer
- Enable firewall protection
- Use antivirus software

## Known Limitations

### Not Suitable For
- **Public internet deployment** - KUYAN has no authentication system
- **Multi-tenant use** - Designed for single-user or trusted family use
- **High-security environments** - Database is not encrypted at rest

### Security Features NOT Included
- ❌ User authentication
- ❌ Database encryption
- ❌ Access control/permissions
- ❌ Audit logging
- ❌ Two-factor authentication

## Threat Model

### What KUYAN Protects Against
- ✅ Data sent to cloud services (no cloud sync)
- ✅ Minimal external dependencies (only exchange rates API, no authentication required)
- ✅ Telemetry and tracking

### What KUYAN Does NOT Protect Against
- ❌ Physical access to your computer
- ❌ Malware on your system
- ❌ Unauthorized network access (if exposed)
- ❌ Database file theft (not encrypted)

## Dependency Security

### Automated Scanning
- Dependencies are regularly reviewed for vulnerabilities
- Consider using `pip-audit` to check for known vulnerabilities:
  ```bash
  pip install pip-audit
  pip-audit -r requirements.txt
  ```

### Minimal Dependencies
KUYAN uses minimal, well-maintained dependencies:
- `streamlit` - Web UI framework
- `pandas` - Data processing
- `plotly` - Visualization
- `requests` - HTTP client
- `python-dateutil` - Date handling

## Security Updates

Security updates will be released as:
- **Patch versions** (1.0.x) for minor security fixes
- **Minor versions** (1.x.0) for significant security improvements

Users are encouraged to:
- Watch the repository for updates
- Subscribe to release notifications
- Update regularly

## Disclaimer

KUYAN is provided "as is" without warranty of any kind. Users are responsible for:
- Securing their own systems
- Backing up their data
- Evaluating security risks for their use case

**Important**: KUYAN is designed for personal/family use in trusted environments. It is NOT designed for:
- Production enterprise use
- Public internet deployment
- Untrusted multi-user environments

---

**Last Updated**: 2025-01-25
