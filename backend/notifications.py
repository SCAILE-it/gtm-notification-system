"""
GTM Notification System - Standalone Module

This module can be used independently or imported into existing applications.
Handles all email notifications with preference checking, retry logic, and audit logging.

Usage:
    from notifications import NotificationSystem

    ns = NotificationSystem(
        resend_api_key="re_xxxxx",
        supabase_url="https://xxx.supabase.co",
        supabase_key="eyJxxxxx"
    )

    await ns.send_job_complete(user_id, job_id, results, csv_data)
"""

from typing import Optional, Dict, List, Any
import os
import asyncio
import base64
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

import resend
from supabase import create_client, Client
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rate_limiter import notification_rate_limiter, RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SCAILE Design System - Email Tokens
# Aligned with zola-aisdkv5 design system for brand consistency
EMAIL_DESIGN = {
    "colors": {
        # Brand colors (converted from oklch to hex for email compatibility)
        "primary": "#282936",          # Dark blue-purple (primary CTA)

        # Semantic colors
        "success": "#10b981",          # Green (job complete)
        "error": "#ef4444",            # Red (job failed)
        "error_hover": "#dc2626",      # Darker red
        "warning": "#f59e0b",          # Amber (quota warning)

        # Neutral palette
        "background": "#fafaf9",       # Warm off-white
        "foreground": "#1f2937",       # Dark gray (primary text)
        "muted": "#6b7280",            # Gray (secondary text)
        "border": "#e5e7eb",           # Light gray (borders)

        # Component backgrounds
        "card": "#ffffff",             # White cards
        "stats_bg": "#f3f4f6",         # Stats grid background
        "error_bg": "#fef2f2",         # Error box background
    },
    "typography": {
        "font_family": '"Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
        "heading_size": "28px",
        "body_size": "16px",
        "small_size": "14px",
        "stat_value_size": "24px",
    },
    "radius": {
        "button": "6px",
    }
}


class NotificationType(str, Enum):
    """Supported notification types"""
    JOB_COMPLETE = "job_complete"
    JOB_FAILED = "job_failed"
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    WELCOME = "welcome"
    VERIFY = "verify"


class EmailStatus(str, Enum):
    """Email delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    FAILED = "failed"


class NotificationSystem:
    """
    Standalone notification system with preference checking, retry logic, and tracking.

    Features:
    - Checks user notification preferences before sending
    - Requires verified email for non-onboarding notifications
    - 2MB threshold for attachments (larger files → storage links)
    - 3x retry with exponential backoff
    - Full audit logging to notification_logs table
    - Resend webhook integration for delivery tracking
    """

    def __init__(
        self,
        resend_api_key: str,
        supabase_url: str,
        supabase_key: str,
        from_email: str = "SCAILE <hello@g-gpt.com>",
        app_url: str = "https://g-gpt.com",
        max_retries: int = 3,
        attachment_size_threshold_mb: int = 2
    ):
        """
        Initialize notification system.

        Args:
            resend_api_key: Resend API key
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            from_email: Default sender email
            app_url: Application URL for links in emails
            max_retries: Number of retry attempts for failed sends
            attachment_size_threshold_mb: Max size for email attachments (larger → storage link)
        """
        self.from_email = from_email
        self.app_url = app_url
        self.max_retries = max_retries
        self.attachment_threshold_bytes = attachment_size_threshold_mb * 1_000_000

        # Initialize clients
        resend.api_key = resend_api_key
        self.supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize Jinja2 template environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        logger.info(f"NotificationSystem initialized with from_email={from_email}")

    async def _check_user_preferences(
        self,
        user_id: str,
        notification_type: NotificationType
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user wants this notification type and if email is verified.

        Returns:
            (should_send: bool, user_email: Optional[str])
        """
        try:
            # Get user email and verification status
            user_response = self.supabase.auth.admin.get_user_by_id(user_id)
            user = user_response.user

            if not user or not user.email:
                logger.warning(f"User {user_id} not found or has no email")
                return False, None

            # For non-onboarding notifications, require verified email
            if notification_type not in [NotificationType.WELCOME, NotificationType.VERIFY]:
                if not user.email_confirmed_at:
                    logger.info(f"User {user_id} email not verified, skipping {notification_type}")
                    return False, None

            # Get user preferences
            prefs_response = self.supabase.table('notification_preferences') \
                .select('*') \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()

            if not prefs_response.data:
                logger.info(f"No preferences found for user {user_id}, using defaults (enabled)")
                return True, user.email

            # Check specific preference
            pref_key = f'email_{notification_type.value}'
            preference_enabled = prefs_response.data.get(pref_key, True)

            if not preference_enabled:
                logger.info(f"User {user_id} disabled {notification_type} notifications")
                return False, None

            return True, user.email

        except Exception as e:
            logger.error(f"Error checking preferences for user {user_id}: {e}")
            # Default to NOT sending if we can't verify preferences
            return False, None

    def _render_template(self, template_name: str, **context) -> str:
        """
        Render email template with design system tokens and context.

        Args:
            template_name: Name of template file (e.g., 'job_complete.html')
            **context: Template variables

        Returns:
            Rendered HTML string
        """
        # Merge design system tokens with context
        template_context = {
            **EMAIL_DESIGN["colors"],
            "colors": EMAIL_DESIGN["colors"],
            "font_family": EMAIL_DESIGN["typography"]["font_family"],
            "heading_size": EMAIL_DESIGN["typography"]["heading_size"],
            "body_size": EMAIL_DESIGN["typography"]["body_size"],
            "small_size": EMAIL_DESIGN["typography"]["small_size"],
            "stat_value_size": EMAIL_DESIGN["typography"]["stat_value_size"],
            "radius": EMAIL_DESIGN["radius"]["button"],
            "app_url": self.app_url,
            **context
        }

        template = self.jinja_env.get_template(template_name)
        return template.render(template_context)

    async def _upload_to_storage(
        self,
        user_id: str,
        job_id: str,
        csv_data: bytes
    ) -> str:
        """
        Upload large CSV to Supabase Storage and return signed URL.

        Returns:
            Signed URL (7-day expiry)
        """
        try:
            storage_path = f"{user_id}/results/{job_id}.csv"

            # Upload to storage
            self.supabase.storage.from_('user-files').upload(
                storage_path,
                csv_data,
                {"content-type": "text/csv", "upsert": "true"}
            )

            # Generate signed URL (7 days)
            signed_response = self.supabase.storage.from_('user-files').create_signed_url(
                storage_path,
                expires_in=604800  # 7 days in seconds
            )

            if 'signedURL' in signed_response:
                logger.info(f"Uploaded {len(csv_data)} bytes to storage: {storage_path}")
                return signed_response['signedURL']
            else:
                raise Exception(f"Failed to create signed URL: {signed_response}")

        except Exception as e:
            logger.error(f"Storage upload failed for job {job_id}: {e}")
            raise

    async def _send_email_with_retry(
        self,
        user_email: str,
        subject: str,
        html: str,
        notification_type: NotificationType,
        user_id: str,
        job_id: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Resend with retry logic and logging.

        Returns:
            {"success": bool, "email_id": Optional[str], "error": Optional[str]}
        """
        email_data = {
            "from": self.from_email,
            "to": [user_email],
            "subject": subject,
            "html": html,
            "tags": [
                {"name": "category", "value": notification_type.value},
                {"name": "user_id", "value": user_id}
            ]
        }

        if job_id:
            email_data["tags"].append({"name": "job_id", "value": job_id})

        if attachments:
            email_data["attachments"] = attachments

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = resend.Emails.send(email_data)

                # Log success to database
                self.supabase.table('notification_logs').insert({
                    "user_id": user_id,
                    "notification_type": notification_type.value,
                    "email_id": result['id'],
                    "recipient_email": user_email,
                    "subject": subject,
                    "status": EmailStatus.SENT.value,
                    "job_id": job_id
                }).execute()

                logger.info(f"Sent {notification_type} email to {user_email}, email_id={result['id']}")
                return {"success": True, "email_id": result['id']}

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff: 5s, 10s, 15s
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    # Final attempt failed, log to database
                    self.supabase.table('notification_logs').insert({
                        "user_id": user_id,
                        "notification_type": notification_type.value,
                        "recipient_email": user_email,
                        "subject": subject,
                        "status": EmailStatus.FAILED.value,
                        "job_id": job_id,
                        "resend_event_data": {"error": last_error}
                    }).execute()

                    logger.error(f"Failed to send {notification_type} email after {self.max_retries} attempts: {last_error}")
                    return {"success": False, "error": last_error}

        return {"success": False, "error": "Unknown error"}

    async def send_job_complete(
        self,
        user_id: str,
        job_id: str,
        results: Dict[str, Any],
        csv_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Send job completion notification.

        Args:
            user_id: User UUID
            job_id: Job/execution UUID
            results: Dict with keys:
                - total_rows: int
                - successful: int
                - failed: int
                - processing_time_seconds: float
            csv_data: Optional CSV bytes (if provided, will attach or upload to storage)

        Returns:
            {"success": bool, "email_id": Optional[str], "reason": Optional[str]}
        """
        # Check preferences
        should_send, user_email = await self._check_user_preferences(
            user_id,
            NotificationType.JOB_COMPLETE
        )

        if not should_send:
            return {"success": False, "reason": "user_preferences_or_unverified_email"}

        # Check rate limit
        try:
            await notification_rate_limiter.check_rate_limit(user_id)
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
            return {"success": False, "reason": "rate_limit_exceeded", "error": str(e)}

        # Handle CSV attachment or storage link
        attachments = None
        download_section = ""

        if csv_data:
            csv_size = len(csv_data)

            if csv_size < self.attachment_threshold_bytes:
                # Small file: attach directly
                attachments = [{
                    "filename": f"results_{job_id}.csv",
                    "content": list(base64.b64encode(csv_data).decode())
                }]
                download_section = f'<p style="color: {EMAIL_DESIGN["colors"]["muted"]};">See attached CSV file.</p>'
            else:
                # Large file: upload to storage and send link
                try:
                    download_url = await self._upload_to_storage(user_id, job_id, csv_data)
                    download_section = f'''
                        <p style="margin: 20px 0;">
                            <a href="{download_url}"
                               style="background: {EMAIL_DESIGN["colors"]["success"]}; color: white; padding: 12px 24px;
                                      text-decoration: none; border-radius: {EMAIL_DESIGN["radius"]["button"]}; display: inline-block;">
                                Download Results (CSV)
                            </a>
                        </p>
                        <p style="color: {EMAIL_DESIGN["colors"]["muted"]}; font-size: {EMAIL_DESIGN["typography"]["small_size"]};">Link expires in 7 days</p>
                    '''
                except Exception as e:
                    logger.error(f"Failed to upload CSV to storage: {e}")
                    download_section = f'<p style="color: {EMAIL_DESIGN["colors"]["error"]};">Error generating download link. Please check the app.</p>'

        # Render email HTML using template
        html = self._render_template(
            "job_complete.html",
            total_rows=results['total_rows'],
            successful=results['successful'],
            failed=results['failed'],
            processing_time_seconds=results['processing_time_seconds'],
            download_section=download_section,
            job_id=job_id
        )

        subject = f"✅ Job Complete: {results['successful']:,}/{results['total_rows']:,} rows processed"

        return await self._send_email_with_retry(
            user_email=user_email,
            subject=subject,
            html=html,
            notification_type=NotificationType.JOB_COMPLETE,
            user_id=user_id,
            job_id=job_id,
            attachments=attachments
        )

    async def send_job_failed(
        self,
        user_id: str,
        job_id: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Send job failure notification.

        Args:
            user_id: User UUID
            job_id: Job UUID
            error_message: Error description

        Returns:
            {"success": bool, "email_id": Optional[str]}
        """
        should_send, user_email = await self._check_user_preferences(
            user_id,
            NotificationType.JOB_FAILED
        )

        if not should_send:
            return {"success": False, "reason": "user_preferences_or_unverified_email"}

        # Check rate limit
        try:
            await notification_rate_limiter.check_rate_limit(user_id)
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
            return {"success": False, "reason": "rate_limit_exceeded", "error": str(e)}

        # Render email HTML using template
        html = self._render_template(
            "job_failed.html",
            error_message=error_message,
            job_id=job_id
        )

        subject = f"❌ Job Failed: {job_id[:8]}"

        return await self._send_email_with_retry(
            user_email=user_email,
            subject=subject,
            html=html,
            notification_type=NotificationType.JOB_FAILED,
            user_id=user_id,
            job_id=job_id
        )

    async def send_quota_warning(
        self,
        user_id: str,
        current_usage: int,
        limit: int
    ) -> Dict[str, Any]:
        """
        Send quota warning (80% usage).

        Args:
            user_id: User UUID
            current_usage: Current API call count
            limit: Monthly limit

        Returns:
            {"success": bool, "email_id": Optional[str]}
        """
        should_send, user_email = await self._check_user_preferences(
            user_id,
            NotificationType.QUOTA_WARNING
        )

        if not should_send:
            return {"success": False, "reason": "user_preferences_or_unverified_email"}

        # Check rate limit
        try:
            await notification_rate_limiter.check_rate_limit(user_id)
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
            return {"success": False, "reason": "rate_limit_exceeded", "error": str(e)}

        percent = (current_usage / limit) * 100
        remaining = limit - current_usage

        # Render email HTML using template
        html = self._render_template(
            "quota_warning.html",
            current_usage=current_usage,
            limit=limit,
            percent=percent,
            remaining=remaining
        )

        subject = f"⚠️ Quota Warning: {percent:.0f}% used ({remaining:,} calls remaining)"

        return await self._send_email_with_retry(
            user_email=user_email,
            subject=subject,
            html=html,
            notification_type=NotificationType.QUOTA_WARNING,
            user_id=user_id
        )


# Convenience functions for easy import

async def notify_job_complete(
    user_id: str,
    job_id: str,
    results: Dict[str, Any],
    csv_data: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Standalone function to send job completion notification.
    Reads configuration from environment variables.

    Example:
        from notifications import notify_job_complete

        await notify_job_complete(
            user_id="user-uuid",
            job_id="job-uuid",
            results={"total_rows": 100, "successful": 98, "failed": 2, "processing_time_seconds": 15.3},
            csv_data=csv_bytes
        )
    """
    ns = NotificationSystem(
        resend_api_key=os.getenv("RESEND_API_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        from_email=os.getenv("FROM_EMAIL", "SCAILE <hello@g-gpt.com>"),
        app_url=os.getenv("APP_URL", "https://g-gpt.com")
    )
    return await ns.send_job_complete(user_id, job_id, results, csv_data)


async def notify_job_failed(user_id: str, job_id: str, error_message: str) -> Dict[str, Any]:
    """Standalone function to send job failure notification"""
    ns = NotificationSystem(
        resend_api_key=os.getenv("RESEND_API_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        from_email=os.getenv("FROM_EMAIL", "SCAILE <hello@g-gpt.com>"),
        app_url=os.getenv("APP_URL", "https://g-gpt.com")
    )
    return await ns.send_job_failed(user_id, job_id, error_message)


async def notify_quota_warning(user_id: str, current_usage: int, limit: int) -> Dict[str, Any]:
    """Standalone function to send quota warning"""
    ns = NotificationSystem(
        resend_api_key=os.getenv("RESEND_API_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        from_email=os.getenv("FROM_EMAIL", "SCAILE <hello@g-gpt.com>"),
        app_url=os.getenv("APP_URL", "https://g-gpt.com")
    )
    return await ns.send_quota_warning(user_id, current_usage, limit)
