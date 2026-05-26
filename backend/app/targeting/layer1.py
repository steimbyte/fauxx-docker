import json
from pathlib import Path
from app.models.enums import CategoryPool

# Weight constants
SELF_REPORTED_CLOSE_WEIGHT = 0.15
DISTANT_WEIGHT = 2.5
NEUTRAL_WEIGHT = 1.0
UNMAPPED_GLOBAL_SUPPRESSION = 0.92


class UserDemographicProfile:
    """User's self-reported demographics"""
    
    def __init__(
        self,
        age_range: str = None,
        gender: str = None,
        profession: str = None,
        region: str = None,
        interests: list[str] = None,
        custom_interests: list[str] = None,
    ):
        self.age_range = age_range
        self.gender = gender
        self.profession = profession
        self.region = region
        self.interests = interests or []
        self.custom_interests = custom_interests or []


class DemographicDistanceMap:
    """
    Maps demographics to category weights using distance rules.
    CLOSE → 0.15, DISTANT → 2.5, NEUTRAL → 1.0
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.rules = self._load_rules()
    
    def _load_rules(self) -> list:
        """Load demographic_distance_rules.json from assets."""
        if not self.assets_path:
            return []
        
        rules_file = self.assets_path / "demographic_distance_rules.json"
        if rules_file.exists():
            with open(rules_file) as f:
                return json.load(f)
        return []
    
    def get_weights(self, profile: UserDemographicProfile | None) -> dict[CategoryPool, float]:
        """Calculate weights based on demographic profile."""
        if not profile:
            return {cat: NEUTRAL_WEIGHT for cat in CategoryPool}
        
        weights = {cat: NEUTRAL_WEIGHT for cat in CategoryPool}
        
        # Apply distance rules based on profile attributes
        # (simplified - full implementation would match rules)
        if profile.age_range:
            weights = self._apply_age_rules(profile.age_range, weights)
        
        if profile.profession:
            weights = self._apply_profession_rules(profile.profession, weights)
        
        if profile.region:
            weights = self._apply_region_rules(profile.region, weights)
        
        return weights
    
    def _apply_age_rules(self, age: str, weights: dict) -> dict:
        """Apply weight adjustments based on age range."""
        # Age-specific adjustments
        return weights
    
    def _apply_profession_rules(self, profession: str, weights: dict) -> dict:
        """Apply weight adjustments based on profession."""
        return weights
    
    def _apply_region_rules(self, region: str, weights: dict) -> dict:
        """Apply weight adjustments based on region."""
        return weights


class SelfReportLayer:
    """
    Layer 1: Self-Reported Demographics
    Weights categories AWAY from user's real interests.
    """
    
    CLOSE_WEIGHT = 0.15
    UNMAPPED_SUPPRESSION = 0.92
    
    def __init__(
        self,
        distance_map: DemographicDistanceMap,
        profile: UserDemographicProfile = None,
    ):
        self.distance_map = distance_map
        self.profile = profile
        self._enabled = True
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def get_weights(self) -> dict[CategoryPool, float]:
        if not self._enabled:
            return {cat: 1.0 for cat in CategoryPool}
        
        # Get distance-based weights
        weights = self.distance_map.get_weights(self.profile)
        
        # Apply custom interest suppressions
        if self.profile and self.profile.custom_interests:
            weights = self._apply_custom_interests(weights)
        
        return weights
    
    def _apply_custom_interests(
        self, 
        weights: dict[CategoryPool, float]
    ) -> dict[CategoryPool, float]:
        """Suppress categories matching user's custom interests."""
        # Map custom interest strings to categories and suppress them
        # Simplified: just apply global suppression
        return {
            cat: w * self.UNMAPPED_SUPPRESSION if cat.value.lower() in 
                 [i.lower() for i in self.profile.custom_interests]
            else w
            for cat, w in weights.items()
        }
