from app.models.enums import CategoryPool
from app.targeting.layer0 import UniformEntropyLayer
from app.targeting.layer1 import SelfReportLayer, DemographicDistanceMap
from app.targeting.layer2 import AdversarialScraperLayer
from app.targeting.layer3 import PersonaRotationLayer, SyntheticPersona
from app.targeting.weight_normalizer import WeightNormalizer


class TargetingEngine:
    """
    Orchestrates all 4 targeting layers.
    
    Layer 0: Uniform Entropy (baseline, always active)
    Layer 1: Self-Report (optional)
    Layer 2: Adversarial Scraper (optional)  
    Layer 3: Persona Rotation (optional)
    
    Final weights = L0 × L1 × L2 × L3, then normalized
    """
    
    def __init__(
        self,
        layer0: UniformEntropyLayer = None,
        layer1: SelfReportLayer = None,
        layer2: AdversarialScraperLayer = None,
        layer3: PersonaRotationLayer = None,
        normalizer: WeightNormalizer = None,
    ):
        self.layer0 = layer0 or UniformEntropyLayer()
        self.layer1 = layer1 or SelfReportLayer(DemographicDistanceMap())
        self.layer2 = layer2 or AdversarialScraperLayer()
        self.layer3 = layer3 or PersonaRotationLayer()
        self.normalizer = normalizer or WeightNormalizer()
        
        self._layer1_enabled = True
        self._layer2_enabled = False
        self._layer3_enabled = True
        
        self._cached_weights = self._compute_weights()
    
    @property
    def cached_weights(self) -> dict[CategoryPool, float]:
        return self._cached_weights
    
    def set_layer1_enabled(self, enabled: bool):
        self._layer1_enabled = enabled
        self._invalidate_cache()
    
    def set_layer2_enabled(self, enabled: bool):
        self._layer2_enabled = enabled
        if self.layer2:
            self.layer2.set_enabled(enabled)
        self._invalidate_cache()
    
    def set_layer3_enabled(self, enabled: bool):
        self._layer3_enabled = enabled
        self.layer3.set_enabled(enabled)
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        self._cached_weights = self._compute_weights()
    
    # Blend ratio: 65% persona, 35% uniform
    PERSONA_BLEND = 0.65
    
    def _compute_weights(self) -> dict[CategoryPool, float]:
        """Compute combined weights.
        
        If Layer 3 (Persona) is enabled: 65% persona, 35% uniform
        If Layer 3 is disabled: 100% uniform
        """
        # Layer 0: uniform baseline
        uniform_weights = self.layer0.get_weights()
        
        if self._layer3_enabled and self.layer3:
            # Persona active: blend 65% persona, 35% uniform
            persona_weights = self.layer3.get_weights()
            blended = {}
            for cat in CategoryPool:
                persona_w = persona_weights.get(cat, 1.0)
                uniform_w = uniform_weights.get(cat, 1.0)
                blended[cat] = (persona_w * self.PERSONA_BLEND) + (uniform_w * (1 - self.PERSONA_BLEND))
        else:
            # Persona disabled: 100% uniform
            blended = uniform_weights
        
        # Apply Layer 1 & 2 multipliers if enabled
        if self._layer1_enabled and self.layer1:
            l1_weights = self.layer1.get_weights()
            blended = {cat: blended[cat] * l1_weights.get(cat, 1.0) for cat in CategoryPool}
        
        if self._layer2_enabled and self.layer2:
            l2_weights = self.layer2.get_weights()
            blended = {cat: blended[cat] * l2_weights.get(cat, 1.0) for cat in CategoryPool}
        
        return self.normalizer.normalize(blended)
    
    def get_weights(self) -> dict[CategoryPool, float]:
        return self.cached_weights
    
    def set_weights(self, weights: dict):
        """Set category weights from a dict."""
        from app.models.enums import CategoryPool
        parsed = {}
        for k, v in weights.items():
            try:
                cat = CategoryPool(k) if isinstance(k, str) else k
                parsed[cat] = float(v)
            except (ValueError, KeyError):
                pass
        self._cached_weights = self.normalizer.normalize(parsed)
    
    def select_category(self) -> CategoryPool:
        """Select a random category based on current weights."""
        weights = self.cached_weights
        categories = list(weights.keys())
        probs = list(weights.values())
        
        import random
        return random.choices(categories, weights=probs, k=1)[0]
