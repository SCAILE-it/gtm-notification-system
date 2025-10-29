"""
Simple sliding window rate limiter for notification system.

This prevents email spam by limiting the number of notifications
a user can receive within a time window.

For production, consider using Redis-backed rate limiting for
distributed systems.
"""

from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """
    Sliding window rate limiter.

    Limits the number of operations per user per time window.
    Thread-safe for async operations.
    """

    def __init__(self, max_calls: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed per window
            window_seconds: Time window in seconds
        """
        self.max_calls = max_calls
        self.window = timedelta(seconds=window_seconds)
        self._calls: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User identifier

        Returns:
            True if within rate limit

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        async with self._lock:
            now = datetime.now()
            cutoff = now - self.window

            # Remove calls outside the current window
            self._calls[user_id] = [
                call_time for call_time in self._calls[user_id]
                if call_time > cutoff
            ]

            # Check if limit exceeded
            if len(self._calls[user_id]) >= self.max_calls:
                oldest_call = self._calls[user_id][0]
                retry_after = (oldest_call + self.window - now).total_seconds()

                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{len(self._calls[user_id])}/{self.max_calls} calls in window. "
                    f"Retry after {retry_after:.0f}s"
                )

                raise RateLimitExceeded(
                    f"Rate limit exceeded. Maximum {self.max_calls} notifications "
                    f"per {self.window.total_seconds():.0f} seconds. "
                    f"Retry after {retry_after:.0f}s."
                )

            # Record this call
            self._calls[user_id].append(now)
            logger.debug(
                f"Rate limit check passed for user {user_id}: "
                f"{len(self._calls[user_id])}/{self.max_calls} calls"
            )

            return True

    async def reset(self, user_id: str) -> None:
        """
        Reset rate limit for a user (admin function).

        Args:
            user_id: User identifier
        """
        async with self._lock:
            if user_id in self._calls:
                del self._calls[user_id]
                logger.info(f"Rate limit reset for user {user_id}")

    async def get_remaining(self, user_id: str) -> int:
        """
        Get remaining calls for user in current window.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining calls
        """
        async with self._lock:
            now = datetime.now()
            cutoff = now - self.window

            # Remove calls outside the current window
            self._calls[user_id] = [
                call_time for call_time in self._calls[user_id]
                if call_time > cutoff
            ]

            return max(0, self.max_calls - len(self._calls[user_id]))

    async def cleanup(self) -> None:
        """
        Clean up old entries (call periodically in production).

        Removes all entries older than the window for all users.
        """
        async with self._lock:
            now = datetime.now()
            cutoff = now - self.window

            users_to_remove = []
            for user_id, calls in self._calls.items():
                # Remove old calls
                self._calls[user_id] = [
                    call_time for call_time in calls
                    if call_time > cutoff
                ]

                # Mark empty users for removal
                if not self._calls[user_id]:
                    users_to_remove.append(user_id)

            # Remove users with no recent calls
            for user_id in users_to_remove:
                del self._calls[user_id]

            logger.debug(f"Cleanup: removed {len(users_to_remove)} inactive users")


# Global rate limiter instance (10 emails per minute per user)
notification_rate_limiter = RateLimiter(max_calls=10, window_seconds=60)
