"""
Rate limiting module - implements sliding window rate limiting for email sends.
Prevents hitting Gmail API rate limits and account suspension.
"""
import time
from collections import deque
from datetime import datetime, timedelta
from src.core.logger import setup_logger
from src.core.config import settings

logger = setup_logger("rate_limiter")


class SlidingWindowRateLimiter:
    """
    Implements sliding window rate limiting for email sends.
    Tracks send attempts within time windows to enforce rate limits.
    """
    
    def __init__(self, max_per_second: float = 0.5, max_per_minute: int = 15, max_per_hour: int = 100):
        """
        Initialize rate limiter with constraints.
        
        Args:
            max_per_second: Maximum sends per second (default 0.5 = 1 email per 2 seconds)
            max_per_minute: Maximum sends per minute (default 15)
            max_per_hour: Maximum sends per hour (default 100)
        """
        self.max_per_second = max_per_second
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        
        # Deques to track timestamps of sent emails
        self.sends = deque()
    
    def can_send(self) -> tuple[bool, str]:
        """
        Check if an email can be sent now.
        Returns (can_send, reason)
        """
        now = datetime.now()
        
        # Remove old entries outside our windows
        cutoff_hour = now - timedelta(hours=1)
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_second = now - timedelta(seconds=1)
        
        # Find the oldest entry we need to keep
        while self.sends and self.sends[0] < cutoff_hour:
            self.sends.popleft()
        
        # Count in different windows
        count_hour = len([t for t in self.sends if t >= cutoff_hour])
        count_minute = len([t for t in self.sends if t >= cutoff_minute])
        count_second = len([t for t in self.sends if t >= cutoff_second])
        
        # Check per-second limit
        if count_second >= self.max_per_second:
            wait_until = self.sends[-1] + timedelta(seconds=1)
            wait_seconds = (wait_until - now).total_seconds()
            return False, f"Per-second limit exceeded ({count_second}/{self.max_per_second}). Wait {wait_seconds:.1f}s"
        
        # Check per-minute limit
        if count_minute >= self.max_per_minute:
            wait_until = self.sends[-1] + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds()
            return False, f"Per-minute limit exceeded ({count_minute}/{self.max_per_minute}). Wait {wait_seconds:.1f}s"
        
        # Check per-hour limit
        if count_hour >= self.max_per_hour:
            wait_until = self.sends[-1] + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()
            return False, f"Per-hour limit exceeded ({count_hour}/{self.max_per_hour}). Wait {wait_seconds:.1f}s"
        
        return True, "OK"
    
    def record_send(self):
        """Record that an email was sent now."""
        self.sends.append(datetime.now())
        logger.debug(f"Email send recorded. Total in window: {len(self.sends)}")
    
    def get_stats(self) -> dict:
        """Get current rate limiting statistics."""
        now = datetime.now()
        cutoff_hour = now - timedelta(hours=1)
        cutoff_minute = now - timedelta(minutes=1)
        cutoff_second = now - timedelta(seconds=1)
        
        count_hour = len([t for t in self.sends if t >= cutoff_hour])
        count_minute = len([t for t in self.sends if t >= cutoff_minute])
        count_second = len([t for t in self.sends if t >= cutoff_second])
        
        return {
            "per_second": {"current": count_second, "limit": self.max_per_second},
            "per_minute": {"current": count_minute, "limit": self.max_per_minute},
            "per_hour": {"current": count_hour, "limit": self.max_per_hour},
        }


# Global rate limiter instance
_rate_limiter: SlidingWindowRateLimiter | None = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        # Read from settings if available, otherwise use defaults
        max_per_second = getattr(settings, 'RATE_LIMIT_PER_SECOND', 0.5)
        max_per_minute = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 15)
        max_per_hour = getattr(settings, 'RATE_LIMIT_PER_HOUR', 100)
        
        _rate_limiter = SlidingWindowRateLimiter(
            max_per_second=max_per_second,
            max_per_minute=max_per_minute,
            max_per_hour=max_per_hour,
        )
        logger.info(
            f"Rate limiter initialized: "
            f"{max_per_second}/s, {max_per_minute}/m, {max_per_hour}/h"
        )
    return _rate_limiter


def check_rate_limit() -> tuple[bool, str]:
    """
    Check if we can send an email now.
    Returns (can_send, message)
    """
    limiter = get_rate_limiter()
    return limiter.can_send()


def record_email_sent():
    """Record that an email was sent."""
    limiter = get_rate_limiter()
    limiter.record_send()


def get_rate_limit_stats() -> dict:
    """Get current rate limiting statistics."""
    limiter = get_rate_limiter()
    return limiter.get_stats()
