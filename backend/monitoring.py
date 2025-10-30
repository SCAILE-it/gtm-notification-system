"""
Error monitoring and tracking integration with Sentry.

This module provides Sentry integration for production error tracking,
performance monitoring, and debugging.
"""

import os
import logging
from typing import Optional, Dict, Any

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    enable_logging: bool = True
) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (Data Source Name). If None, reads from SENTRY_DSN env var
        environment: Environment name (production, staging, development)
        traces_sample_rate: Percentage of transactions to trace (0.0 - 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 - 1.0)
        enable_logging: Whether to capture logging events

    Returns:
        True if Sentry was initialized successfully, False otherwise

    Example:
        >>> from monitoring import init_sentry
        >>> init_sentry()  # Uses SENTRY_DSN from environment
        True
    """
    if not SENTRY_AVAILABLE:
        logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk")
        return False

    # Get DSN from parameter or environment
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.info("Sentry DSN not configured. Skipping Sentry initialization.")
        return False

    try:
        integrations = []

        # Add logging integration if enabled
        if enable_logging:
            integrations.append(
                LoggingIntegration(
                    level=logging.INFO,       # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
            )

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=integrations,
            # Release tracking (optional - set via SENTRY_RELEASE env var)
            release=os.getenv("SENTRY_RELEASE"),
            # Additional options
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,  # Include stack traces
        )

        logger.info(f"Sentry initialized successfully (environment={environment})")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error"
) -> Optional[str]:
    """
    Capture an exception and send to Sentry.

    Args:
        error: The exception to capture
        context: Additional context (user_id, job_id, etc.)
        level: Severity level (fatal, error, warning, info, debug)

    Returns:
        Event ID if successful, None otherwise

    Example:
        >>> try:
        ...     send_email(...)
        ... except Exception as e:
        ...     capture_exception(e, context={"user_id": "123", "email_type": "job_complete"})
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        logger.warning(f"Sentry not available. Exception: {error}")
        return None

    try:
        # Set context if provided
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, {"value": value})

                # Set level
                scope.level = level

                # Capture the exception
                event_id = sentry_sdk.capture_exception(error)
                logger.debug(f"Exception captured in Sentry: {event_id}")
                return event_id
        else:
            event_id = sentry_sdk.capture_exception(error)
            logger.debug(f"Exception captured in Sentry: {event_id}")
            return event_id

    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")
        return None


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add a breadcrumb for debugging context.

    Breadcrumbs are events leading up to an error that help with debugging.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "email", "database", "api")
        level: Severity (info, warning, error, debug)
        data: Additional structured data

    Example:
        >>> add_breadcrumb("Sending job complete email", category="email", data={"user_id": "123"})
        >>> add_breadcrumb("Email sent successfully", category="email", level="info")
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return

    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except Exception as e:
        logger.debug(f"Failed to add breadcrumb: {e}")


def set_user(user_id: str, email: Optional[str] = None) -> None:
    """
    Set user context for error tracking.

    Args:
        user_id: User identifier
        email: User email (optional)

    Example:
        >>> set_user("user-123", "user@example.com")
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return

    try:
        sentry_sdk.set_user({"id": user_id, "email": email})
    except Exception as e:
        logger.debug(f"Failed to set user context: {e}")


def set_tag(key: str, value: str) -> None:
    """
    Set a tag for error filtering and grouping.

    Args:
        key: Tag key
        value: Tag value

    Example:
        >>> set_tag("notification_type", "job_complete")
        >>> set_tag("email_provider", "resend")
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.Hub.current.client:
        return

    try:
        sentry_sdk.set_tag(key, value)
    except Exception as e:
        logger.debug(f"Failed to set tag: {e}")


# Auto-initialize Sentry if SENTRY_DSN is set
if os.getenv("SENTRY_DSN"):
    init_sentry(
        environment=os.getenv("SENTRY_ENVIRONMENT", "production")
    )
