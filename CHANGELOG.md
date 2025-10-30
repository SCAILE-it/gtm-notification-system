# Changelog

All notable changes to the SCAILE Notification System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-01-29

### 🎉 Initial Release

The first production-ready release of the SCAILE Notification System. A standalone, fully testable email notification system for SCAILE (GTM Intelligence Copilot).

### ✨ Added

#### Core Features
- **Email Notifications** - Send job completion, failure, and quota warnings via Resend
- **Job Complete Notifications** - With results summary and CSV attachments
- **Job Failed Notifications** - With error details and debugging info
- **Quota Warning Notifications** - Alert users at 80% usage
- **User Preference Management** - Granular controls for each notification type
- **Email Delivery Tracking** - Track sent, delivered, opened, clicked, bounced, complained
- **Webhook Integration** - Resend webhooks update delivery status automatically
- **Audit Logging** - Complete notification history in `notification_logs` table

#### Technical Features
- **Jinja2 Email Templates** - Maintainable, designer-friendly templates
  - `base.html` - Reusable base template
  - `job_complete.html` - Job completion with stats grid
  - `job_failed.html` - Error display with code formatting
  - `quota_warning.html` - Usage progress bar
- **Rate Limiting** - Prevent email spam (10 emails/min per user)
  - Sliding window algorithm
  - Async-safe implementation
  - Configurable limits
- **Sentry Integration** - Production error monitoring
  - Auto-capture exceptions
  - Breadcrumbs for debugging
  - User/tag context
- **Smart File Handling** - 2MB threshold for attachments vs storage links
- **Retry Logic** - 3x retry with exponential backoff (5s, 10s, 15s)
- **Email Verification** - Require verified email for non-onboarding notifications

#### Database Schema
- **notification_preferences** table
  - Per-notification type toggles
  - Digest frequency settings
  - Auto-created on user signup
- **notification_logs** table
  - Complete audit trail
  - Delivery tracking fields
  - Resend webhook data storage
- **RLS Policies** - Users can only see their own data
- **Indexes** - Optimized for common queries
- **Helper Functions** - `get_user_notification_stats()` for analytics

#### Testing
- **Unit Tests** - 434 lines of pytest tests
- **Integration Tests** - Full workflow testing
- **Docker Compose Environment** - Local Supabase + MailHog
  - PostgreSQL (Supabase-compatible)
  - MailHog (email testing)
  - Auth service
  - Storage service
  - PostgREST API
- **Test Scripts** - `test_full_flow.py` for end-to-end validation
- **Reset Script** - One-command database reset

#### Documentation
- **README.md** - Architecture overview and quick start
- **QUICKSTART.md** - 10-minute setup guide
- **docs/API.md** - Complete API reference (627 lines)
- **docs/INTEGRATION_GUIDE.md** - Step-by-step integration (557 lines)
- **docs/EMAIL_VISUAL_CHECKLIST.md** - Email QA checklist (343 lines)
- **ROADMAP.md** - Product vision through v3.0.0
- **CHANGELOG.md** - This file

#### Developer Experience
- **Standalone Development** - No dependencies on main app
- **Easy Integration** - Copy `notifications.py` and run migration
- **Convenience Functions** - `notify_job_complete()`, `notify_job_failed()`, `notify_quota_warning()`
- **Type Hints** - Full TypeScript-style typing
- **SCAILE Design System** - Consistent branding and colors
- **Environment Variables** - `.env.example` with all options

### 🛠️ Technical Details

#### Dependencies
```
resend==2.6.0
supabase==2.11.2
pydantic==2.10.6
jinja2==3.1.4
sentry-sdk==2.22.0
pytest==8.3.4
```

#### Architecture
```
User → NotificationSystem → Check Preferences → Rate Limit
                          ↓
                    Render Template → Send via Resend → Log to DB
                          ↓
                    Resend Webhooks → Update Status
```

#### Tech Stack
- **Backend:** Python 3.12+
- **Database:** PostgreSQL (Supabase)
- **Email:** Resend API
- **Templates:** Jinja2
- **Testing:** Pytest + Docker Compose
- **Monitoring:** Sentry
- **Frontend:** React/Next.js (components)
- **Edge Functions:** Deno/TypeScript

### 🔒 Security

- **RLS Policies** - Database-level access control
- **Webhook Signature Verification** - Svix-based signature validation
- **Email Verification** - Required for non-onboarding notifications
- **Rate Limiting** - Prevent abuse and spam
- **Service Role Isolation** - Backend uses service role, frontend uses anon key
- **No PII in Logs** - Sensitive data excluded from error tracking

### 📊 Performance

- **Async/Await** - Non-blocking throughout
- **Connection Pooling** - Supabase client connection pooling
- **Smart Attachment Handling** - Auto-switch to storage for large files
- **Efficient Retry** - Exponential backoff prevents thundering herd
- **Indexed Queries** - All common queries use indexes

### 🐛 Bug Fixes

None - initial release.

### 🚀 Deployment

**GitHub Repository:** https://github.com/SCAILE-it/gtm-notification-system

**Installation:**
```bash
git clone https://github.com/SCAILE-it/gtm-notification-system.git
cd gtm-notification-system/backend
pip install -r requirements.txt
```

**Quick Test:**
```bash
docker-compose up -d
python tests/test_full_flow.py
```

### 📦 What's Included

```
gtm-notification-system/
├── backend/
│   ├── notifications.py          # Main module (687 lines)
│   ├── rate_limiter.py           # Rate limiting (150 lines)
│   ├── monitoring.py             # Sentry integration (200 lines)
│   ├── templates/                # Jinja2 email templates
│   │   ├── base.html
│   │   ├── job_complete.html
│   │   ├── job_failed.html
│   │   └── quota_warning.html
│   ├── tests/                    # Unit tests
│   └── requirements.txt
├── supabase/
│   ├── functions/
│   │   ├── resend-webhook/       # Webhook handler
│   │   └── send-welcome-email/   # Onboarding email
│   └── migrations/
│       ├── 00_setup_auth_mock.sql
│       └── 20250128_notification_tables.sql
├── frontend/
│   └── components/
│       ├── NotificationPreferences.tsx
│       └── EmailStatsCard.tsx
├── tests/
│   └── test_full_flow.py         # Integration tests
├── scripts/
│   ├── reset_local_db.sh
│   └── send_test_emails.py
├── docs/
│   ├── API.md
│   ├── INTEGRATION_GUIDE.md
│   └── EMAIL_VISUAL_CHECKLIST.md
├── docker-compose.yml
├── README.md
├── QUICKSTART.md
├── ROADMAP.md
├── CHANGELOG.md
└── .env.example
```

**Total Lines of Code:** ~5,830

### 🙏 Acknowledgments

- **SCAILE Team** - For the vision and requirements
- **Resend** - Excellent email API
- **Supabase** - Fantastic backend platform
- **Jinja2** - Powerful templating
- **Sentry** - Best-in-class error tracking

### 📝 Notes

This is an **alpha release** ready for isolated testing. Integrate into production after thorough testing.

**Recommended Next Steps:**
1. Set up Resend account and verify domain
2. Run integration tests: `docker-compose up && python tests/test_full_flow.py`
3. Send test emails: `python scripts/send_test_emails.py`
4. Review email rendering in Gmail, Outlook, Apple Mail
5. Deploy Edge Functions to Supabase
6. Run migration on production database
7. Integrate into main SCAILE application

---

## [Unreleased]

### Planned for v1.1.0

- Welcome email implementation
- Email unsubscribe links (CAN-SPAM compliance)
- Environment variable validation with Pydantic
- Admin metrics dashboard (React)
- CI/CD with GitHub Actions
- Enhanced structured logging

See [ROADMAP.md](ROADMAP.md) for full feature roadmap.

---

## Release Types

- **Major (x.0.0):** Breaking changes, major features
- **Minor (x.x.0):** New features, backwards compatible
- **Patch (x.x.x):** Bug fixes, security patches

---

## Links

- **Repository:** https://github.com/SCAILE-it/gtm-notification-system
- **Issues:** https://github.com/SCAILE-it/gtm-notification-system/issues
- **Discussions:** https://github.com/SCAILE-it/gtm-notification-system/discussions
- **SCAILE:** https://g-gpt.com

---

**Legend:**
- ✨ Added - New features
- 🛠️ Changed - Changes to existing functionality
- 🗑️ Deprecated - Features to be removed
- 🐛 Fixed - Bug fixes
- 🔒 Security - Security improvements
- 📊 Performance - Performance improvements

---

*Generated with ❤️ by the SCAILE Team*
