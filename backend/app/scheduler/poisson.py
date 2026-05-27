import random
import math
from datetime import datetime


class PoissonScheduler:
    """
    Schedules poison actions using Poisson distribution.
    Mimics the timing behavior from Fauxx Android app.
    """
    
    def __init__(self):
        self.LOCAL_SIGMA = 0.2  # Lognormal multiplier sigma
    
    @staticmethod
    def lognormal_multiplier() -> float:
        """Generate lognormal random multiplier (0.5 - 1.5 range)."""
        u = random.gauss(0, 1)
        return math.exp(u * 0.2)
    
    def poisson_delay(self, actions_per_hour: float) -> int:
        """
        Calculate delay for Poisson-distributed events.
        Returns delay in milliseconds.
        
        For high rates (e.g., 10,000/hr = ~2.78/sec):
        - Lower bound is 100ms to prevent overwhelming the system
        - At 10,000/hr, average delay is 360ms, with jitter ~180-540ms
        """
        if actions_per_hour <= 0:
            return 3600000  # 1 hour default
        
        # Average interval in hours
        avg_interval_hours = 1.0 / actions_per_hour
        
        # Add jitter using lognormal distribution
        jitter = self.lognormal_multiplier()
        
        # Convert to milliseconds
        delay_ms = int(avg_interval_hours * 3600000 * jitter)
        
        # Minimum 100ms for high rates, 1000ms for low rates
        if actions_per_hour >= 3600:  # 3600+ = 1+/sec
            return max(100, delay_ms)  # 100ms min for high rates
        else:
            return max(1000, delay_ms)  # 1 second min for low rates
    
    def next_delay_ms(
        self,
        actions_per_hour: int,
        prev_category: str = None,
        next_category: str = None,
        allowed_start: int = 7,
        allowed_end: int = 23,
    ) -> int:
        """
        Calculate next action delay respecting allowed hours.
        
        Args:
            actions_per_hour: Target rate (12=LOW, 60=MEDIUM, 200=HIGH)
            prev_category: Previous category (for correlation)
            next_category: Next category (for correlation)
            allowed_start: Start of allowed hours (0-23)
            allowed_end: End of allowed hours (0-23)
        
        Returns:
            Delay in milliseconds until next action
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Check if within allowed hours
        if not self._is_within_allowed_hours(current_hour, allowed_start, allowed_end):
            # Wait until start of next allowed window
            return self._ms_until_hour(now, allowed_start)
        
        # Poisson delay for action rate
        base_delay = self.poisson_delay(actions_per_hour)
        
        return base_delay
    
    def _is_within_allowed_hours(
        self,
        current_hour: int,
        start: int,
        end: int
    ) -> bool:
        """Check if current hour is within allowed window."""
        if start <= end:
            # Normal case: e.g., 7-23
            return start <= current_hour < end
        else:
            # Overnight case: e.g., 22-6
            return current_hour >= start or current_hour < end
    
    def _ms_until_hour(self, now: datetime, target_hour: int) -> int:
        """Calculate milliseconds until next occurrence of target hour."""
        target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        
        if target <= now:
            # Next day
            from datetime import timedelta
            target += timedelta(days=1)
        
        return int((target - now).total_seconds() * 1000)
