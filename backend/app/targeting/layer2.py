import json
from pathlib import Path
from app.models.enums import CategoryPool
from typing import Set


class AdversarialScraperLayer:
    """
    Layer 2: Adversarial Scraper
    Weights categories AGAINST what ad platforms think they know about you.
    Scrapes Google Ads Settings and Facebook Ad Preferences.
    
    CONFIRMED_WEIGHT = 0.05 (suppress what they know)
    ABSENT_WEIGHT = 3.0 (boost what they don't know)
    """
    
    CONFIRMED_WEIGHT = 0.05
    ABSENT_WEIGHT = 3.0
    NEUTRAL_WEIGHT = 1.0
    STALE_THRESHOLD_MS = 7 * 24 * 60 * 60 * 1000  # 7 days
    
    def __init__(self, platform_profiles: dict = None):
        self.platform_profiles = platform_profiles or {}
        self._enabled = False
        self._cached_weights = None
        self._last_update = 0
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self._recompute_weights()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def get_weights(self) -> dict[CategoryPool, float]:
        if not self._enabled:
            return {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
        
        # Check if stale
        import time
        now = int(time.time() * 1000)
        if now - self._last_update > self.STALE_THRESHOLD_MS:
            # Data is stale, revert to neutral
            return {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
        
        return self._cached_weights or {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
    
    def update_platform_profile(self, platform: str, categories: Set[CategoryPool]):
        """Update a platform's known interest profile."""
        self.platform_profiles[platform] = categories
        self._last_update = int(__import__("time").time() * 1000)
        if self._enabled:
            self._recompute_weights()
    
    def _recompute_weights(self):
        """Recompute weights based on all platform profiles."""
        # Collect all confirmed interests
        confirmed = set()
        for cats in self.platform_profiles.values():
            confirmed.update(cats)
        
        weights = {}
        for cat in CategoryPool:
            if cat in confirmed:
                # They know this about us - suppress it heavily
                weights[cat] = self.CONFIRMED_WEIGHT
            else:
                # They don't know this - boost it
                weights[cat] = self.ABSENT_WEIGHT
        
        self._cached_weights = weights
    
    def clear_profiles(self):
        """Clear all platform profiles."""
        self.platform_profiles.clear()
        self._cached_weights = None
        self._last_update = 0
