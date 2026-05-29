from collections import deque
import time
from threading import RLock

class RateLimiter:
    def __init__(self, max_calls, period_seconds):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.timestamps = deque()
        self.lock = RLock()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.monotonic()
                
                # Remove timestamps older than the period
                while self.timestamps and self.timestamps[0] <= now - self.period_seconds:
                    self.timestamps.popleft()
                
                if len(self.timestamps) >= self.max_calls:
                    sleep_time = self.timestamps[0] - (now - self.period_seconds)
                    if sleep_time > 0:
                        # Inform the user/system that we are waiting
                        print(f"Rate limit hit. Waiting for {sleep_time:.2f} seconds.")
                        time.sleep(sleep_time)
                
                # After waiting (or if not rate-limited), proceed
                self.timestamps.append(time.monotonic())
            
            return func(*args, **kwargs)
        return wrapper
