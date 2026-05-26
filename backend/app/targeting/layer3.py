from app.models.enums import CategoryPool
from dataclasses import dataclass
from typing import Set
import random
import time


@dataclass
class SyntheticPersona:
    """A synthetic identity for noise generation."""
    id: str
    name: str
    age_range: str
    profession: str
    region: str
    interests: Set[CategoryPool]
    created_at: int
    active_until: int

    @classmethod
    def create(
        cls,
        name: str,
        age_range: str,
        profession: str,
        region: str,
        interests: Set[CategoryPool],
        active_days: int = 7,
    ) -> "SyntheticPersona":
        now = int(time.time() * 1000)
        jitter = random.randint(1, 3) * 24 * 60 * 60 * 1000  # 1-3 days jitter
        active_until = now + (active_days * 24 * 60 * 60 * 1000) + jitter
        
        return cls(
            id=f"persona_{now}",
            name=name,
            age_range=age_range,
            profession=profession,
            region=region,
            interests=interests,
            created_at=now,
            active_until=active_until,
        )


class PersonaRotationLayer:
    """
    Layer 3: Synthetic Persona Rotation
    Rotates persona every ~7 days for temporal coherence.
    """
    
    ALIGNED_WEIGHT = 2.0
    MISALIGNED_WEIGHT = 0.3
    NEUTRAL_WEIGHT = 1.0
    PERSONA_FOLLOW_FRACTION = 0.70
    
    def __init__(self, persona: SyntheticPersona = None):
        self._persona = persona
        self._enabled = True
        self._weights = {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def get_weights(self) -> dict[CategoryPool, float]:
        if not self._enabled:
            return {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
        return dict(self._weights)
    
    def set_persona(self, persona: SyntheticPersona):
        self._persona = persona
        self._recompute_weights()
    
    def _recompute_weights(self):
        """Recompute weights based on current persona."""
        if not self._persona:
            self._weights = {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
            return
        
        weights = {}
        for cat in CategoryPool:
            if cat in self._persona.interests:
                # 70% chance to follow persona interest with high weight
                if random.random() < self.PERSONA_FOLLOW_FRACTION:
                    weights[cat] = self.ALIGNED_WEIGHT
                else:
                    weights[cat] = self.NEUTRAL_WEIGHT
            else:
                # 70% chance to suppress non-persona interests
                if random.random() < self.PERSONA_FOLLOW_FRACTION:
                    weights[cat] = self.MISALIGNED_WEIGHT
                else:
                    weights[cat] = self.NEUTRAL_WEIGHT
        
        self._weights = weights
    
    def is_expired(self) -> bool:
        """Check if current persona has expired."""
        if not self._persona:
            return True
        now = int(time.time() * 1000)
        return now >= self._persona.active_until


class PersonaGenerator:
    """
    Generates synthetic personas based on templates.
    """
    
    MAX_ATTEMPTS = 10
    BASE_ROTATION_DAYS = 7
    ROTATION_JITTER_DAYS = (1, 3)
    
    def __init__(self, templates: list = None):
        self.templates = templates or self._default_templates()
    
    @staticmethod
    def _default_templates() -> list:
        """Default persona templates."""
        return [
            {
                "name": "Alex Thompson",
                "age_range": "25-34",
                "profession": "Software Engineer",
                "region": "US-West",
                "interests": ["TECHNOLOGY", "GAMING", "FITNESS", "MUSIC"],
            },
            {
                "name": "Sarah Miller",
                "age_range": "35-44",
                "profession": "Marketing Manager",
                "region": "UK",
                "interests": ["BUSINESS", "TRAVEL", "FASHION", "FOOD"],
            },
            {
                "name": "Michael Chen",
                "age_range": "18-24",
                "profession": "Student",
                "region": "Canada",
                "interests": ["ENTERTAINMENT", "GAMING", "MUSIC", "SPORTS"],
            },
        ]
    
    def generate(self, weight_hints: dict[CategoryPool, float] = None) -> SyntheticPersona:
        """Generate a new synthetic persona."""
        # Try to find a template that doesn't conflict with hints
        for _ in range(self.MAX_ATTEMPTS):
            template = random.choice(self.templates)
            
            # Map template interests to CategoryPool
            interests = set()
            for interest_str in template.get("interests", []):
                try:
                    interests.add(CategoryPool[interest_str])
                except KeyError:
                    pass
            
            persona = SyntheticPersona.create(
                name=template["name"],
                age_range=template["age_range"],
                profession=template["profession"],
                region=template["region"],
                interests=interests,
            )
            return persona
        
        # Fallback
        return SyntheticPersona.create(
            name="Alex Johnson",
            age_range="25-34",
            profession="Professional",
            region="US",
            interests=set(random.sample(list(CategoryPool), 5)),
        )
    
    @staticmethod
    def next_rotation_time() -> int:
        """Calculate next rotation timestamp."""
        jitter = random.randint(*PersonaGenerator.ROTATION_JITTER_DAYS)
        days = PersonaGenerator.BASE_ROTATION_DAYS + jitter
        now = int(time.time() * 1000)
        return now + (days * 24 * 60 * 60 * 1000)
