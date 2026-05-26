import random
from app.targeting.engine import TargetingEngine
from app.models.enums import CategoryPool


class ActionDispatcher:
    """
    Selects next action category based on targeting weights.
    """
    
    def __init__(self, engine: TargetingEngine):
        self.engine = engine
    
    def select_category(self) -> CategoryPool:
        """Select a category using weighted sampling."""
        weights = self.engine.get_weights()
        categories = list(weights.keys())
        probs = list(weights.values())
        
        return random.choices(categories, weights=probs, k=1)[0]
    
    def weighted_sample(
        self,
        items: list,
        weights: dict
    ) -> any:
        """Sample from weighted distribution."""
        if not items:
            return None
        
        cats = list(weights.keys())
        probs = [weights.get(c, 0) for c in cats]
        
        selected = random.choices(items, weights=probs, k=1)[0]
        return selected
