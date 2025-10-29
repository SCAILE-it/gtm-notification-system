# GTM Notification System - Integration Guide

**How to integrate the standalone notification system into gtm-power-app**

---

## 📋 Prerequisites

Before integrating, ensure you have:

- ✅ Tested the notification system in isolation
- ✅ All tests passing (`pytest backend/tests/` and `docker-compose up`)
- ✅ Resend account with API key
- ✅ Resend domain verified
- ✅ Supabase project ready

---

## 🔧 Step 1: Backend Integration (Modal.com)

### 1.1 Copy Notification Module

```bash
# From gtm-notification-system directory
cp backend/notifications.py ../gtm-power-app-backend/
```

### 1.2 Install Dependencies

Add to `gtm-power-app-backend/requirements.txt`:

```
resend==2.6.0
supabase==2.11.2
```

Or in your Modal image definition:

```python
# In g-mcp-tools-complete.py
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        # ... existing dependencies ...
        "resend==2.6.0",
        "supabase==2.11.2",
    )
)
```

### 1.3 Add Secrets to Modal

```bash
# Add Resend API key
modal secret create resend-api-key \
  RESEND_API_KEY=re_xxxxx

# Add Supabase credentials (if not already added)
modal secret create supabase-creds \
  SUPABASE_URL=https://xxxxx.supabase.co \
  SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
```

### 1.4 Update g-mcp-tools-complete.py

```python
# At top of file
from notifications import notify_job_complete, notify_job_failed

# Update your Modal function to include the new secrets
@app.function(
    image=image,
    timeout=3600,
    secrets=[
        modal.Secret.from_name("gemini-secret"),
        modal.Secret.from_name("resend-api-key"),  # ADD THIS
        modal.Secret.from_name("supabase-creds")   # ADD THIS
    ]
)
async def bulk_enrich(request: BulkRequest):
    # ... existing job processing code ...

    # AFTER job completes successfully:
    try:
        await notify_job_complete(
            user_id=request.user_id,  # Make sure BulkRequest has user_id field
            job_id=batch_id,
            results={
                "total_rows": total_rows,
                "successful": successful,
                "failed": failed,
                "processing_time_seconds": processing_time
            },
            csv_data=results_csv_bytes  # Optional: your CSV results
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        # Don't fail the job if notification fails

    # AFTER job fails:
    try:
        await notify_job_failed(
            user_id=request.user_id,
            job_id=batch_id,
            error_message=str(error)
        )
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")

    return response
```

### 1.5 Update BulkRequest Model

```python
# Add user_id to your Pydantic request model
class BulkRequest(BaseModel):
    rows: List[Dict[str, Any]]
    tools: List[str]
    user_id: str  # ADD THIS FIELD
```

### 1.6 Deploy

```bash
modal deploy g-mcp-tools-complete.py
```

---

## 💾 Step 2: Database Migration (Supabase)

### 2.1 Copy Migration File

```bash
# From gtm-notification-system directory
cp supabase/migrations/20250128_notification_tables.sql \
   ../gtm-power-app-frontend/supabase/migrations/
```

### 2.2 Run Migration

```bash
cd ../gtm-power-app-frontend

# Option A: Local Supabase
npx supabase db push

# Option B: Remote Supabase
npx supabase db push --db-url "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"
```

### 2.3 Verify Tables Created

```sql
-- Run in Supabase SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('notification_preferences', 'notification_logs');

-- Should return 2 rows
```

---

## 🌐 Step 3: Edge Functions (Supabase)

### 3.1 Copy Edge Functions

```bash
# From gtm-notification-system directory
cd ../gtm-power-app-frontend

# Copy webhook handler
cp -r ../gtm-notification-system/supabase/functions/resend-webhook \
      supabase/functions/

# Copy welcome email function
cp -r ../gtm-notification-system/supabase/functions/send-welcome-email \
      supabase/functions/

# Copy shared utilities
cp -r ../gtm-notification-system/supabase/functions/_shared \
      supabase/functions/
```

### 3.2 Set Environment Variables

```bash
# Add secrets to Supabase
npx supabase secrets set RESEND_API_KEY=re_xxxxx
npx supabase secrets set RESEND_WEBHOOK_SECRET=whsec_xxxxx
npx supabase secrets set FROM_EMAIL="SCAILE <hello@g-gpt.com>"
npx supabase secrets set APP_URL=https://g-gpt.com
npx supabase secrets set DOCS_URL=https://docs.g-gpt.com
```

### 3.3 Deploy Edge Functions

```bash
# Deploy webhook handler
npx supabase functions deploy resend-webhook

# Deploy welcome email function
npx supabase functions deploy send-welcome-email
```

### 3.4 Configure Resend Webhooks

1. Go to Resend Dashboard → Webhooks
2. Add new webhook:
   - **URL:** `https://[your-project].supabase.co/functions/v1/resend-webhook`
   - **Events:** Select all:
     - `email.sent`
     - `email.delivered`
     - `email.delivery_delayed`
     - `email.complained`
     - `email.bounced`
     - `email.opened`
     - `email.clicked`
3. Copy webhook secret
4. Add to Supabase: `npx supabase secrets set RESEND_WEBHOOK_SECRET=whsec_xxxxx`

### 3.5 Test Webhook

```bash
# Send test webhook
curl -X POST https://[project].supabase.co/functions/v1/resend-webhook \
  -H "Content-Type: application/json" \
  -H "svix-id: test" \
  -H "svix-timestamp: $(date +%s)" \
  -H "svix-signature: test" \
  -d '{
    "type": "email.delivered",
    "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "data": {
      "email_id": "test-email-123",
      "from": "hello@g-gpt.com",
      "to": ["test@example.com"]
    }
  }'
```

---

## ⚛️ Step 4: Frontend Components (Next.js)

### 4.1 Copy Components

```bash
# From gtm-notification-system directory
cd ../gtm-power-app-frontend

# Create notifications directory
mkdir -p components/notifications

# Copy components
cp ../gtm-notification-system/frontend/components/NotificationPreferences.tsx \
   components/notifications/

cp ../gtm-notification-system/frontend/components/EmailStatsCard.tsx \
   components/notifications/
```

### 4.2 Create Notifications Settings Page

```tsx
// app/profile/notifications/page.tsx
import { NotificationPreferences } from '@/components/notifications/NotificationPreferences'
import { createClient } from '@/lib/supabase/server'

export default async function NotificationsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="container max-w-4xl py-8">
      <h1 className="text-3xl font-bold mb-2">Notification Settings</h1>
      <p className="text-muted-foreground mb-8">
        Manage how and when you receive notifications
      </p>

      <NotificationPreferences supabaseClient={supabase} userId={user.id} />
    </div>
  )
}
```

### 4.3 Add Email Stats to Dashboard

```tsx
// app/profile/stats/page.tsx
import { EmailStatsCard } from '@/components/notifications/EmailStatsCard'
import { createClient } from '@/lib/supabase/server'

export default async function StatsPage() {
  const supabase = await createClient()

  return (
    <div className="container max-w-6xl py-8">
      <h1 className="text-3xl font-bold mb-8">Email Activity</h1>
      <EmailStatsCard supabaseClient={supabase} limit={20} />
    </div>
  )
}
```

### 4.4 Update Navigation

Add link to notification settings in your profile menu:

```tsx
// components/layout/ProfileMenu.tsx
<DropdownMenuItem asChild>
  <Link href="/profile/notifications">
    <Bell className="mr-2 h-4 w-4" />
    Notification Settings
  </Link>
</DropdownMenuItem>
```

---

## 🧪 Step 5: Testing Integration

### 5.1 Test Welcome Email

1. Create a new user account
2. Check that `notification_preferences` row was auto-created
3. Check that welcome email was sent
4. Verify `notification_logs` entry was created

```sql
-- Verify preferences created
SELECT * FROM notification_preferences WHERE user_id = '[new-user-id]';

-- Verify welcome email logged
SELECT * FROM notification_logs
WHERE user_id = '[new-user-id]' AND notification_type = 'welcome';
```

### 5.2 Test Job Notification

1. Run a bulk job with `user_id` in the request
2. Wait for job to complete
3. Check email inbox for job completion email
4. Verify notification_logs entry:

```sql
SELECT * FROM notification_logs
WHERE user_id = '[user-id]' AND notification_type = 'job_complete'
ORDER BY created_at DESC LIMIT 1;
```

### 5.3 Test Webhook Tracking

1. Send a job notification
2. Open the email
3. Wait 30 seconds
4. Check if `opened_at` was updated:

```sql
SELECT email_id, status, sent_at, delivered_at, opened_at
FROM notification_logs
WHERE user_id = '[user-id]'
ORDER BY created_at DESC LIMIT 1;
```

### 5.4 Test User Preferences

1. Go to `/profile/notifications`
2. Disable "Job completed" notifications
3. Run a job
4. Verify NO email was sent
5. Check logs:

```sql
SELECT * FROM notification_logs
WHERE user_id = '[user-id]' AND notification_type = 'job_complete'
ORDER BY created_at DESC LIMIT 1;

-- Should be empty or have older timestamp
```

---

## 🚨 Troubleshooting

### Issue: Emails Not Sending

**Check:**
1. `RESEND_API_KEY` is set in Modal secrets
2. Resend domain is verified
3. `FROM_EMAIL` domain matches verified domain
4. Check Modal logs: `modal app logs g-mcp-tools-fast --follow`

**Debug:**
```python
# Add logging to your job
logger.info(f"Attempting to send notification to user {user_id}")
result = await notify_job_complete(...)
logger.info(f"Notification result: {result}")
```

### Issue: Webhooks Not Working

**Check:**
1. Webhook URL is correct in Resend dashboard
2. `RESEND_WEBHOOK_SECRET` matches in Supabase
3. Edge Function is deployed
4. Check Edge Function logs in Supabase dashboard

**Test manually:**
```bash
# Send test event
curl -X POST https://[project].supabase.co/functions/v1/resend-webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "email.delivered", "data": {"email_id": "test"}}'
```

### Issue: Preferences Not Saving

**Check:**
1. RLS policies are enabled
2. User is authenticated
3. Check browser console for errors
4. Verify `notification_preferences` table exists

**Debug:**
```sql
-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'notification_preferences';

-- Check policies exist
SELECT * FROM pg_policies
WHERE tablename = 'notification_preferences';
```

### Issue: Large Files Not Attaching

**Check:**
1. Supabase Storage bucket `user-files` exists
2. Bucket RLS policies allow user uploads
3. File size threshold (default 2MB)

**Create storage bucket:**
```sql
-- In Supabase SQL Editor
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-files', 'user-files', false);
```

---

## ✅ Integration Checklist

Before marking integration complete, verify:

- [ ] Backend module copied and deployed
- [ ] Modal secrets configured
- [ ] Database migration ran successfully
- [ ] Edge Functions deployed
- [ ] Resend webhooks configured
- [ ] Frontend components added
- [ ] Navigation links updated
- [ ] Welcome email sends on signup
- [ ] Job complete email sends after job
- [ ] Preferences page loads and saves
- [ ] Stats dashboard shows data
- [ ] Webhook tracking updates status
- [ ] User can opt-out of notifications
- [ ] Emails respect opt-out preferences

---

## 📊 Post-Integration Monitoring

### Key Metrics to Track

```sql
-- Daily email volume
SELECT
  DATE(sent_at) as date,
  notification_type,
  COUNT(*) as count
FROM notification_logs
WHERE sent_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(sent_at), notification_type
ORDER BY date DESC;

-- Delivery rates
SELECT
  notification_type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE delivered_at IS NOT NULL) as delivered,
  COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opened,
  COUNT(*) FILTER (WHERE clicked_at IS NOT NULL) as clicked,
  COUNT(*) FILTER (WHERE bounced_at IS NOT NULL) as bounced
FROM notification_logs
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY notification_type;

-- User engagement
SELECT
  user_id,
  COUNT(*) as emails_sent,
  COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as emails_opened,
  MAX(opened_at) as last_opened
FROM notification_logs
GROUP BY user_id
ORDER BY emails_sent DESC
LIMIT 10;
```

---

## 🔄 Rollback Plan

If integration causes issues:

### Quick Rollback

```bash
# 1. Remove notification calls from backend
# In g-mcp-tools-complete.py, comment out:
# await notify_job_complete(...)

# 2. Redeploy without notifications
modal deploy g-mcp-tools-complete.py

# 3. Disable Edge Functions (optional)
# In Supabase dashboard → Edge Functions → Disable
```

### Full Rollback

```sql
-- Remove database tables
DROP TABLE IF EXISTS notification_logs CASCADE;
DROP TABLE IF EXISTS notification_preferences CASCADE;

-- Remove triggers
DROP TRIGGER IF EXISTS on_auth_user_created_notification_prefs ON auth.users;
DROP FUNCTION IF EXISTS create_default_notification_preferences();
```

---

**Integration complete!** 🎉

Your notification system is now live. Monitor the metrics above and adjust preferences/templates as needed.
