# SCAILE Notification System - Quickstart Guide

**Get the notification system running in 10 minutes!**

---

## 🚀 Quick Setup

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Resend account (free tier OK)
- Supabase project (or use local)

---

## Step 1: Clone & Setup (2 min)

```bash
# Navigate to the project
cd gtm-notification-system

# Install Python dependencies
cd backend
pip install -r requirements.txt
cd ..
```

---

## Step 2: Configure Environment (3 min)

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your keys
nano .env
```

**Required variables:**
```bash
RESEND_API_KEY=re_xxxxx          # Get from resend.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
FROM_EMAIL=hello@yourdomain.com  # Must match verified domain in Resend
```

---

## Step 3: Start Testing Environment (1 min)

**NEW: Use the automated reset script!**

```bash
# One command to reset database and start fresh
./scripts/reset_local_db.sh
```

This script:
- ✅ Stops existing containers
- ✅ Removes old database volumes
- ✅ Starts all services (Postgres, MailHog, Auth, Storage)
- ✅ Runs migrations automatically (auth mock + notification tables)
- ✅ Seeds 3 test users
- ✅ Verifies setup

**Alternative (manual):**
```bash
# Start all services
docker-compose up -d

# Wait for postgres
sleep 10

# Migrations run automatically via docker-compose volumes
# Check services are healthy
docker-compose ps
```

You should see all services as "healthy":
- ✅ postgres (port 5432)
- ✅ mailhog (port 8025 - web UI)
- ✅ auth (port 9999)
- ✅ rest (port 3000)
- ✅ storage (port 5000)

**NOTE:** Migrations now include auth mock schema (00_setup_auth_mock.sql) which creates test users for local testing

---

## Step 4: Test the System (2 min)

### Option A: Run Integration Tests

```bash
python tests/test_full_flow.py
```

You should see:
```
✓ PostgreSQL is running
✓ MailHog is healthy
✓ PostgREST is healthy
...
ALL TESTS PASSED ✓
```

### Option B: Test Manually

```python
# test_manual.py
import asyncio
from backend.notifications import notify_job_complete

async def test():
    result = await notify_job_complete(
        user_id="test-user-123",
        job_id="test-job-456",
        results={
            "total_rows": 100,
            "successful": 95,
            "failed": 5,
            "processing_time_seconds": 12.3
        }
    )
    print(f"Success: {result['success']}")
    print(f"Email ID: {result.get('email_id')}")

asyncio.run(test())
```

Run it:
```bash
python test_manual.py
```

**Check email in MailHog:**
Open http://localhost:8025 in your browser. You should see the job completion email!

---

## Step 5: View Results

### Check MailHog Web UI
http://localhost:8025

You'll see all test emails sent. Click to view HTML rendered email.

### Check Database Logs

```bash
docker exec -it gtm-notifications-postgres psql -U postgres -d postgres -c "SELECT * FROM notification_logs;"
```

You should see entries with:
- `email_id`
- `status: 'sent'`
- `notification_type: 'job_complete'`

---

## 🎨 Visual Email Verification (Optional but Recommended)

**Send real test emails via Resend to verify SCAILE branding:**

### Prerequisites
1. Get Resend API key from [resend.com](https://resend.com/api-keys) (free tier OK)
2. Add to `.env`:
   ```bash
   RESEND_API_KEY=re_your_actual_key
   TEST_RECIPIENT_EMAIL=your-email@example.com
   ```

### Send Test Emails

```bash
# Interactive script - sends 3 real emails
python scripts/send_test_emails.py
```

This sends:
1. ✅ Job Complete email
2. ❌ Job Failed email
3. ⚠️  Quota Warning email

### Verify in Your Email Client

Check your inbox and verify using the comprehensive checklist:

📋 **See:** `docs/EMAIL_VISUAL_CHECKLIST.md`

**Quick checks:**
- ✅ SCAILE branding (not "GTM Power App")
- ✅ Colors match design system (#282936 primary)
- ✅ Links point to g-gpt.com
- ✅ Footer shows "SCAILE - GTM Intelligence Copilot"
- ✅ Mobile rendering works
- ✅ Dark mode compatible

**Test in multiple clients:**
- Gmail (web + mobile)
- Outlook (web + desktop)
- Apple Mail

---

## 🎯 Next Steps

### Production Setup

1. **Get Resend API Key:**
   - Go to [resend.com](https://resend.com)
   - Sign up (free tier: 100 emails/day)
   - Verify your domain
   - Get API key

2. **Set Up Resend Webhooks:**
   - In Resend dashboard → Webhooks
   - Add webhook URL: `https://[project].supabase.co/functions/v1/resend-webhook`
   - Select all events
   - Copy webhook secret
   - Add to Supabase secrets: `npx supabase secrets set RESEND_WEBHOOK_SECRET=whsec_xxxxx`

3. **Deploy Edge Functions:**
   ```bash
   cd supabase
   npx supabase functions deploy resend-webhook
   npx supabase functions deploy send-welcome-email
   ```

4. **Run Migration on Production:**
   ```bash
   npx supabase db push
   ```

5. **Integrate into Your App:**
   See `docs/INTEGRATION_GUIDE.md` for step-by-step instructions.

---

## 🧪 Testing Tips

### Unit Tests

```bash
# Run all unit tests
cd backend
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=notifications --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
python tests/test_full_flow.py

# Check logs
docker-compose logs -f postgres
docker-compose logs -f mailhog
```

### Manual Testing with MailHog

1. Start services: `docker-compose up -d`
2. Open MailHog UI: http://localhost:8025
3. Run your notification code
4. Check MailHog for email
5. Click email to see HTML rendered

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your code
result = await notify_job_complete(...)
```

---

## 🔧 Common Issues

### Issue: Services not starting

**Solution:**
```bash
# Check Docker is running
docker ps

# Restart services
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs
```

### Issue: Migration fails

**Solution:**
```bash
# Check Postgres is ready
docker exec gtm-notifications-postgres pg_isready

# Manually run migration
docker exec -i gtm-notifications-postgres psql -U postgres -d postgres < supabase/migrations/20250128_notification_tables.sql
```

### Issue: Emails not showing in MailHog

**Solution:**
```bash
# Check MailHog is running
curl http://localhost:8025

# Check SMTP port is accessible
telnet localhost 1025

# View MailHog logs
docker-compose logs mailhog
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📊 Verify Setup Checklist

Before integrating into production:

- [ ] Docker services all running (green)
- [ ] Database migration completed successfully
- [ ] Unit tests passing (`pytest tests/`)
- [ ] Integration tests passing (`python tests/test_full_flow.py`)
- [ ] Emails visible in MailHog (http://localhost:8025)
- [ ] Notification logs in database
- [ ] Resend account created and domain verified
- [ ] Resend API key configured
- [ ] Resend webhook configured
- [ ] Edge Functions deployed to Supabase

---

## 🚀 Ready to Integrate?

Follow the detailed integration guide:

```bash
cat docs/INTEGRATION_GUIDE.md
```

Or jump to specific sections:
- **Backend:** See `docs/INTEGRATION_GUIDE.md#step-1-backend-integration`
- **Database:** See `docs/INTEGRATION_GUIDE.md#step-2-database-migration`
- **Frontend:** See `docs/INTEGRATION_GUIDE.md#step-4-frontend-components`

---

## 📚 Additional Resources

- **API Documentation:** `docs/API.md`
- **Integration Guide:** `docs/INTEGRATION_GUIDE.md`
- **Example Code:** `tests/test_notifications.py`
- **Docker Compose:** `docker-compose.yml`

---

## 🎉 Success!

If you made it here, your notification system is ready to test!

**Next:** Integrate into your main application following `docs/INTEGRATION_GUIDE.md`

**Questions?** Check the troubleshooting section above or open an issue.

---

**Built for SCAILE** - GTM Intelligence Copilot
