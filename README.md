<img width="1344" height="768" alt="Gemini_Generated_Image_zfuz92zfuz92zfuz" src="https://github.com/user-attachments/assets/e94bdad1-fc74-4a52-8745-a05aacb466e6" />
GameDB Authentication System

A premium, modern authentication engine built with Flask and MariaDB, featuring secure password hashing, session management, and a robust password recovery system.
🚀 Features

    Secure Authentication: Powered by Flask-Login and Bcrypt (Salted Hashing).

    Dynamic UI: Single-page responsive interface with real-time password strength validation.

    Password Recovery: Secure, timed reset tokens via itsdangerous with SMTP or Resend API delivery.

    Database: Structured MariaDB/MySQL schema with unique constraints and data normalization.

    Production Ready: Pre-configured for deployment on Railway using Gunicorn.

🛠️ Tech Stack

    Backend: Python (Flask)

    Database: MariaDB / MySQL

    Frontend: HTML5, CSS3 (Modern Glassmorphism), JavaScript (ES6)

    DevOps: Docker, Ngrok (for local testing), Railway (Production)

💻 Local Setup (Kali Linux)

🚢 Deployment (Railway)

### Email Backend Notes (Important for Railway Free Plan)

Railway free plan blocks outbound SMTP, so password reset emails should use HTTPS API delivery.

Set these environment variables:

```env
EMAIL_BACKEND=resend
RESEND_API_KEY=your_resend_api_key
RESEND_FROM_EMAIL=no-reply@your-verified-domain.com
MAIL_TIMEOUT=8
```

Optional:

```env
RESEND_API_BASE=https://api.resend.com
```

If `EMAIL_BACKEND` is not set, the app auto-selects:
- `resend` when `RESEND_API_KEY` exists
- `smtp` otherwise

  Contributing

Contributions are welcome! Please fork the repo, make your changes, and submit a pull request.
