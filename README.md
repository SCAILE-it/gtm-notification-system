# SCAILE Notification System

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

**Standalone email notification system for SCAILE (GTM Intelligence Copilot)**

[Quick Start](#-quick-start) •
[Documentation](docs/) •
[Roadmap](ROADMAP.md) •
[Contributing](CONTRIBUTING.md) •
[Changelog](CHANGELOG.md)

</div>

---

## 🎯 Purpose

This is an **isolated, fully testable** notification system that can be developed and tested independently, then plugged into the main SCAILE application when ready.

## 📦 What's Included

- **Backend** (Python/Modal.com) - Job completion, failure, and quota notifications
- **Supabase Edge Functions** (Deno/TypeScript) - Onboarding emails + webhook handling
- **Frontend Components** (React/Next.js) - User preferences + email stats dashboard
- **Database Schema** - notification_preferences + notification_logs tables
- **Tests** - Unit + integration tests with Docker Compose

## 🏗️ Architecture

```
User Job Completes (Modal) → Check Preferences → Send via Resend → Log to DB
                                                      ↓
                                          Resend Webhooks → Update Status
                                                      ↓
                                          Frontend Dashboard Shows Stats
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker (for integration tests)
- Resend API key
- Supabase project (or use local)

### Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Supabase
cd ../supabase
npm install -g supabase

# Frontend
cd ../frontend
npm install
```

### Run Tests

```bash
# Unit tests
cd backend
pytest tests/

# Integration tests (starts local Supabase + MailHog)
cd ..
docker-compose up
python tests/test_full_flow.py
```

## 📁 Project Structure

```
gtm-notification-system/
├── backend/
│   ├── notifications.py          # Main notification module
│   ├── resend_client.py          # Resend API wrapper
│   ├── supabase_client.py        # Supabase client wrapper
│   ├── templates/                # Email HTML templates
│   ├── tests/                    # Unit tests
│   └── requirements.txt
│
├── supabase/
│   ├── functions/
│   │   ├── resend-webhook/       # Handle Resend events
│   │   └── send-welcome-email/   # Onboarding emails
│   └── migrations/
│       └── 20250128_notification_tables.sql
│
├── frontend/
│   └── components/
│       ├── NotificationPreferences.tsx
│       └── EmailStatsCard.tsx
│
├── tests/
│   ├── test_full_flow.py         # End-to-end tests
│   └── conftest.py               # Test fixtures
│
├── docs/
│   ├── INTEGRATION_GUIDE.md      # How to integrate into main app
│   └── API.md                    # API documentation
│
├── docker-compose.yml            # Local testing environment
└── .env.example                  # Environment variables template
```

## 🔌 Integration into Main App

Once tested, integration is simple:

```bash
# 1. Copy backend module
cp backend/notifications.py ../gtm-power-app-backend/

# 2. Add one line to your job executor
await notify_job_complete(user_id, job_id, results, csv_data)

# 3. Copy frontend components
cp frontend/components/* ../gtm-power-app-frontend/components/notifications/

# 4. Run database migration
npx supabase db push

# Done!
```

See [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for detailed steps.

## 🧪 Testing Strategy

### Local Development
- Mock Resend API with MailHog (no real emails sent)
- Local Supabase (Docker) - no production database access
- Isolated Next.js app for component testing

### Integration Tests
- Simulates full workflow: job complete → email sent → webhook received → status updated
- Tests preferences (user opt-out scenarios)
- Tests retry logic (Resend failures)
- Tests file size thresholds (attach vs. storage link)

## 📊 Features

### Notifications Supported
- ✅ Job completion (with CSV attachment or download link)
- ✅ Job failure (error details)
- ✅ Quota warning (80% usage)
- ✅ Quota exceeded
- ✅ Welcome email (onboarding)
- ✅ Email verification

### Tracking
- ✅ Email sent timestamp
- ✅ Delivered (Resend webhook)
- ✅ Opened (tracking pixel)
- ✅ Clicked (link tracking)
- ✅ Bounced (invalid email)
- ✅ Complained (spam report)

### User Controls
- ✅ Granular preferences (toggle each notification type)
- ✅ Email verification requirement
- ✅ Email stats dashboard

## 🔐 Security

- ✅ Webhook signature verification
- ✅ RLS on notification tables
- ✅ Email verification for non-onboarding notifications
- ✅ Audit logging for compliance

## 📈 Performance

- ✅ 3x retry with exponential backoff
- ✅ Async/await throughout
- ✅ Database connection pooling
- ✅ 2MB threshold for attachments (auto-switches to storage links)

## 📝 Environment Variables

```bash
# Resend
RESEND_API_KEY=re_xxxxx
RESEND_WEBHOOK_SECRET=whsec_xxxxx

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx

# Email sender
FROM_EMAIL="SCAILE <hello@g-gpt.com>"
```

## 📚 Documentation

- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Step-by-step integration into main app
- [API Documentation](docs/API.md) - Function signatures and examples
- [Database Schema](supabase/migrations/20250128_notification_tables.sql) - Table structures

## 🤝 Contributing

This is an isolated module. To make changes:

1. Update code in this repo
2. Run tests: `pytest backend/tests/`
3. Run integration tests: `docker-compose up && python tests/test_full_flow.py`
4. Update main app when ready

## 📄 License

Same as parent SCAILE project

---

---

## 🌟 What's New in v1.0.0

- ✅ **Jinja2 Templates** - Designer-friendly email templates
- ✅ **Rate Limiting** - Prevent email spam (10/min per user)
- ✅ **Sentry Integration** - Production error monitoring
- ✅ **Comprehensive Docs** - ROADMAP, CHANGELOG, CONTRIBUTING
- ✅ **GitHub Repository** - https://github.com/SCAILE-it/gtm-notification-system

**Status:** ✅ Production Ready (v1.0.0)
**Last Updated:** 2025-01-29

---

## 📚 Links

- **Repository:** https://github.com/SCAILE-it/gtm-notification-system
- **Issues:** https://github.com/SCAILE-it/gtm-notification-system/issues
- **Discussions:** https://github.com/SCAILE-it/gtm-notification-system/discussions
- **SCAILE:** https://g-gpt.com

---

**Built with ❤️ by the SCAILE Team**
