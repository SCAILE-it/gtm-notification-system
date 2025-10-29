# GTM Notification System - API Documentation

**Version:** 1.0
**Last Updated:** 2025-01-28

---

## Table of Contents

1. [NotificationSystem Class](#notificationsystem-class)
2. [Notification Methods](#notification-methods)
3. [Convenience Functions](#convenience-functions)
4. [Type Definitions](#type-definitions)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## NotificationSystem Class

### Constructor

```python
NotificationSystem(
    resend_api_key: str,
    supabase_url: str,
    supabase_key: str,
    from_email: str = "SCAILE <hello@g-gpt.com>",
    app_url: str = "https://g-gpt.com",
    max_retries: int = 3,
    attachment_size_threshold_mb: int = 2
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `resend_api_key` | `str` | ✅ | - | Resend API key |
| `supabase_url` | `str` | ✅ | - | Supabase project URL |
| `supabase_key` | `str` | ✅ | - | Supabase service role key |
| `from_email` | `str` | ❌ | `SCAILE <hello@g-gpt.com>` | Sender email address |
| `app_url` | `str` | ❌ | `https://g-gpt.com` | Application URL for links |
| `max_retries` | `int` | ❌ | `3` | Number of retry attempts |
| `attachment_size_threshold_mb` | `int` | ❌ | `2` | Max size (MB) for email attachments |

**Example:**

```python
from notifications import NotificationSystem

ns = NotificationSystem(
    resend_api_key="re_xxxxx",
    supabase_url="https://xxx.supabase.co",
    supabase_key="eyJxxxxx"
)
```

---

## Notification Methods

### send_job_complete()

Send job completion notification with results.

```python
async def send_job_complete(
    user_id: str,
    job_id: str,
    results: Dict[str, Any],
    csv_data: Optional[bytes] = None
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | `str` | ✅ | User UUID |
| `job_id` | `str` | ✅ | Job/execution UUID |
| `results` | `dict` | ✅ | Job results (see below) |
| `csv_data` | `bytes` | ❌ | Optional CSV results |

**Results Dictionary:**

```python
{
    "total_rows": int,           # Total rows processed
    "successful": int,           # Successfully processed rows
    "failed": int,               # Failed rows
    "processing_time_seconds": float  # Execution time
}
```

**Return Value:**

```python
{
    "success": bool,
    "email_id": str,  # Resend email ID (if successful)
    "reason": str     # Failure reason (if success=False)
}
```

**Behavior:**
- ✅ Checks user notification preferences
- ✅ Requires verified email
- ✅ Attaches CSV if < 2MB
- ✅ Uploads to storage and sends link if > 2MB
- ✅ Retries up to 3 times on failure
- ✅ Logs to `notification_logs` table

**Example:**

```python
result = await ns.send_job_complete(
    user_id="user-uuid-123",
    job_id="job-uuid-456",
    results={
        "total_rows": 1000,
        "successful": 987,
        "failed": 13,
        "processing_time_seconds": 45.2
    },
    csv_data=csv_bytes  # Optional
)

if result['success']:
    print(f"Email sent: {result['email_id']}")
else:
    print(f"Failed: {result['reason']}")
```

---

### send_job_failed()

Send job failure notification.

```python
async def send_job_failed(
    user_id: str,
    job_id: str,
    error_message: str
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | `str` | ✅ | User UUID |
| `job_id` | `str` | ✅ | Job UUID |
| `error_message` | `str` | ✅ | Error description |

**Return Value:**

```python
{
    "success": bool,
    "email_id": str,  # Resend email ID (if successful)
    "reason": str     # Failure reason (if success=False)
}
```

**Example:**

```python
result = await ns.send_job_failed(
    user_id="user-uuid-123",
    job_id="job-uuid-456",
    error_message="Database connection timeout after 30s"
)
```

---

### send_quota_warning()

Send quota warning (80% usage).

```python
async def send_quota_warning(
    user_id: str,
    current_usage: int,
    limit: int
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | `str` | ✅ | User UUID |
| `current_usage` | `int` | ✅ | Current API call count |
| `limit` | `int` | ✅ | Monthly limit |

**Return Value:**

```python
{
    "success": bool,
    "email_id": str,
    "reason": str
}
```

**Example:**

```python
# Send when user hits 80% of quota
result = await ns.send_quota_warning(
    user_id="user-uuid-123",
    current_usage=8000,
    limit=10000
)
```

---

## Convenience Functions

For quick usage without creating a `NotificationSystem` instance.

### notify_job_complete()

```python
from notifications import notify_job_complete

result = await notify_job_complete(
    user_id="user-uuid",
    job_id="job-uuid",
    results={...},
    csv_data=csv_bytes
)
```

Reads configuration from environment variables:
- `RESEND_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FROM_EMAIL` (optional)
- `APP_URL` (optional)

### notify_job_failed()

```python
from notifications import notify_job_failed

result = await notify_job_failed(
    user_id="user-uuid",
    job_id="job-uuid",
    error_message="Error details"
)
```

### notify_quota_warning()

```python
from notifications import notify_quota_warning

result = await notify_quota_warning(
    user_id="user-uuid",
    current_usage=8000,
    limit=10000
)
```

---

## Type Definitions

### NotificationType (Enum)

```python
class NotificationType(str, Enum):
    JOB_COMPLETE = "job_complete"
    JOB_FAILED = "job_failed"
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    WELCOME = "welcome"
    VERIFY = "verify"
```

### EmailStatus (Enum)

```python
class EmailStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    FAILED = "failed"
```

---

## Error Handling

### Common Errors

**User Not Found:**
```python
{
    "success": False,
    "reason": "user_not_found"
}
```

**Email Not Verified:**
```python
{
    "success": False,
    "reason": "user_preferences_or_unverified_email"
}
```

**User Opted Out:**
```python
{
    "success": False,
    "reason": "user_preferences_or_unverified_email"
}
```

**Resend API Error:**
```python
{
    "success": False,
    "error": "API rate limit exceeded"
}
```

### Exception Handling

```python
try:
    result = await ns.send_job_complete(...)
    if not result['success']:
        logger.warning(f"Notification not sent: {result.get('reason')}")
except Exception as e:
    logger.error(f"Notification system error: {e}")
    # Job should continue even if notification fails
```

**Best Practice:** Always wrap notification calls in try-except and don't fail the main operation if notification fails.

---

## Examples

### Example 1: Modal.com Integration

```python
# In g-mcp-tools-complete.py
import modal
from notifications import notify_job_complete

app = modal.App("my-app")

@app.function(
    secrets=[
        modal.Secret.from_name("resend-api-key"),
        modal.Secret.from_name("supabase-creds")
    ]
)
async def process_bulk_job(user_id: str, job_id: str, data: list):
    # Process job
    results = process_data(data)

    # Generate CSV
    csv_data = generate_csv(results)

    # Send notification
    try:
        await notify_job_complete(
            user_id=user_id,
            job_id=job_id,
            results={
                "total_rows": len(data),
                "successful": results['success_count'],
                "failed": results['error_count'],
                "processing_time_seconds": results['duration']
            },
            csv_data=csv_data
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        # Continue - don't fail job if notification fails

    return results
```

### Example 2: FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from notifications import notify_job_complete

app = FastAPI()

async def send_completion_email(user_id: str, job_id: str, results: dict):
    """Background task to send notification"""
    await notify_job_complete(
        user_id=user_id,
        job_id=job_id,
        results=results
    )

@app.post("/jobs/{job_id}/complete")
async def mark_job_complete(
    job_id: str,
    results: dict,
    background_tasks: BackgroundTasks
):
    # Mark job as complete in database
    update_job_status(job_id, "completed", results)

    # Send notification in background
    background_tasks.add_task(
        send_completion_email,
        user_id=get_user_from_job(job_id),
        job_id=job_id,
        results=results
    )

    return {"status": "completed"}
```

### Example 3: Celery Task Integration

```python
from celery import Celery
from notifications import notify_job_complete
import asyncio

app = Celery('tasks')

@app.task
def process_bulk_data(user_id, job_id, data):
    # Process data
    results = process_data(data)

    # Send notification (run async in sync context)
    asyncio.run(notify_job_complete(
        user_id=user_id,
        job_id=job_id,
        results=results
    ))

    return results
```

### Example 4: Error Handling with Retry

```python
import asyncio
from notifications import notify_job_failed

async def safe_notify_error(user_id: str, job_id: str, error: str, retries=3):
    """Send error notification with custom retry logic"""
    for attempt in range(retries):
        try:
            result = await notify_job_failed(
                user_id=user_id,
                job_id=job_id,
                error_message=error
            )

            if result['success']:
                return True

            # User opted out or email not verified
            if 'preferences' in result.get('reason', ''):
                logger.info(f"User {user_id} has notifications disabled")
                return False

        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Failed to send error notification after {retries} attempts: {e}")
                return False

            await asyncio.sleep(5 * (attempt + 1))

    return False
```

---

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from notifications import NotificationSystem

@pytest.mark.asyncio
async def test_job_complete_notification():
    with patch('resend.Emails.send') as mock_send:
        mock_send.return_value = {'id': 'email_test123'}

        ns = NotificationSystem(
            resend_api_key="test_key",
            supabase_url="https://test.supabase.co",
            supabase_key="test_key"
        )

        # Mock Supabase client
        ns.supabase = create_mock_supabase()

        result = await ns.send_job_complete(
            user_id="test-user",
            job_id="test-job",
            results={
                "total_rows": 100,
                "successful": 95,
                "failed": 5,
                "processing_time_seconds": 10.0
            }
        )

        assert result['success'] is True
        assert 'email_id' in result
```

### Integration Testing

See `tests/test_full_flow.py` for complete integration tests using Docker Compose.

---

## Rate Limiting

Resend has rate limits:
- **Free tier:** 100 emails/day
- **Paid tier:** 50,000 emails/month

**Recommendations:**
- Use digest mode for high-volume users
- Implement application-level rate limiting
- Monitor usage via `notification_logs` table

```sql
-- Check daily email volume
SELECT
    DATE(sent_at) as date,
    COUNT(*) as emails_sent
FROM notification_logs
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(sent_at)
ORDER BY date DESC;
```

---

## Best Practices

1. **Always check return value:**
   ```python
   result = await notify_job_complete(...)
   if not result['success']:
       logger.warning(f"Notification failed: {result.get('reason')}")
   ```

2. **Don't fail main operation:**
   ```python
   try:
       await notify_job_complete(...)
   except Exception as e:
       logger.error(f"Notification error: {e}")
       # Continue with main flow
   ```

3. **Use background tasks:**
   ```python
   # In FastAPI
   background_tasks.add_task(notify_job_complete, ...)
   ```

4. **Monitor delivery rates:**
   ```sql
   SELECT
       notification_type,
       COUNT(*) as total,
       COUNT(*) FILTER (WHERE delivered_at IS NOT NULL) as delivered,
       COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opened
   FROM notification_logs
   GROUP BY notification_type;
   ```

5. **Respect user preferences:**
   - System automatically checks preferences
   - Users can opt-out via settings page
   - Unverified emails don't receive notifications (except onboarding)

---

## Changelog

### Version 1.0 (2025-01-28)
- ✅ Initial release
- ✅ Job completion notifications
- ✅ Job failure notifications
- ✅ Quota warning notifications
- ✅ User preference support
- ✅ Email verification requirement
- ✅ Resend webhook tracking
- ✅ 2MB attachment threshold with storage fallback
- ✅ 3x retry with exponential backoff
- ✅ Comprehensive logging

---

## Support

- **Documentation:** This file + `/docs/INTEGRATION_GUIDE.md`
- **Issues:** Report via GitHub Issues
- **Examples:** See `tests/` directory

---

**Built with:** Resend API | Supabase | Python 3.12+
