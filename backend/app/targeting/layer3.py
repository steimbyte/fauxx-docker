from app.models.enums import CategoryPool
from dataclasses import dataclass
from typing import Set, Optional
import random
import time
import json
import os

# Pre-defined persona pool (32 personas covering all 32 categories)
PERSONA_POOL = [
    {
        "name": "Tech-Conscious Millennial",
        "age_range": "25-34",
        "profession": "Software Developer",
        "region": "West Coast",
        "interests": ["Technology", "Gaming", "Science", "Fitness"],
        "behaviors": ["Night Owl", "Early Adopter", "Privacy-Conscious"]
    },
    {
        "name": "Finance-Focused Professional",
        "age_range": "35-44",
        "profession": "Investment Banker",
        "region": "New York",
        "interests": ["Finance", "Business", "Entertainment", "Travel"],
        "behaviors": ["Early Riser", "Data-Driven", "Risk-Aware"]
    },
    {
        "name": "Health-Conscious Parent",
        "age_range": "35-44",
        "profession": "Physician",
        "region": "Midwest",
        "interests": ["Medical", "Fitness", "Parenting", "Wellness"],
        "behaviors": ["Detail-Oriented", "Research-Heavy", "Wellness-Focused"]
    },
    {
        "name": "World-Traveling Digital Nomad",
        "age_range": "28-38",
        "profession": "Freelance Designer",
        "region": "Remote",
        "interests": ["Travel", "Crafts", "Technology", "Entertainment"],
        "behaviors": ["Spontaneous", "Location-Independent", "Culturally-Curious"]
    },
    {
        "name": "Foodie & Home Chef",
        "age_range": "30-40",
        "profession": "Restaurant Critic",
        "region": "San Francisco",
        "interests": ["Food", "Cooking", "Travel", "Crafts"],
        "behaviors": ["Aesthetic-Focused", "Quality-Seeker", "Social-Diner"]
    },
    {
        "name": "Hardcore Gamer",
        "age_range": "18-28",
        "profession": "Twitch Streamer",
        "region": "Texas",
        "interests": ["Gaming", "Technology", "Music", "Entertainment"],
        "behaviors": ["Night Owl", "Competitive", "Community-Focused"]
    },
    {
        "name": "Fashion-Forward Influencer",
        "age_range": "22-32",
        "profession": "Fashion Blogger",
        "region": "Los Angeles",
        "interests": ["Fashion", "Beauty", "Travel", "Crafts"],
        "behaviors": ["Trend-Savvy", "Visual-First", "Social-Media-Active"]
    },
    {
        "name": "Marathon Runner & Sports Fan",
        "age_range": "30-45",
        "profession": "Athletic Coach",
        "region": "Colorado",
        "interests": ["Sports", "Fitness", "Outdoor", "Travel"],
        "behaviors": ["Disciplined", "Goal-Oriented", "Outdoor-Enthusiast"]
    },
    {
        "name": "Vinyl Collector & Music Producer",
        "age_range": "28-40",
        "profession": "Music Producer",
        "region": "Nashville",
        "interests": ["Music", "Fashion", "Entertainment", "Gaming"],
        "behaviors": ["Audiophile", "Creative", "Nostalgic"]
    },
    {
        "name": "Cinephile & Movie Critic",
        "age_range": "25-38",
        "profession": "Film Journalist",
        "region": "New York",
        "interests": ["Entertainment", "History", "Crafts", "Music"],
        "behaviors": ["Analytical", "Pop-Culture-Literate", "Opinionated"]
    },
    {
        "name": "Bookworm & Academic",
        "age_range": "35-50",
        "profession": "University Professor",
        "region": "Boston",
        "interests": ["Academic", "History", "Science", "Politics"],
        "behaviors": ["Analytical", "Research-Oriented", "Intellectual"]
    },
    {
        "name": "Contemporary Art Enthusiast",
        "age_range": "30-45",
        "profession": "Gallery Curator",
        "region": "Chicago",
        "interests": ["Crafts", "Music", "Fashion", "Travel"],
        "behaviors": ["Culturally-Engaged", "Aesthetic-Sensitive", "Collector"]
    },
    {
        "name": "Science Communicator",
        "age_range": "28-38",
        "profession": "Science Writer",
        "region": "Seattle",
        "interests": ["Science", "Technology", "Academic", "Entertainment"],
        "behaviors": ["Evidence-Based", "Curious", "Public-Education-Focused"]
    },
    {
        "name": "EdTech Advocate",
        "age_range": "32-42",
        "profession": "EdTech Product Manager",
        "region": "Austin",
        "interests": ["Academic", "Technology", "Business", "Entertainment"],
        "behaviors": ["Innovation-Driven", "Impact-Focused", "Data-Literate"]
    },
    {
        "name": "Startup Founder",
        "age_range": "28-38",
        "profession": "Entrepreneur",
        "region": "Silicon Valley",
        "interests": ["Business", "Technology", "Finance", "Entertainment"],
        "behaviors": ["Growth-Minded", "Risk-Tolerant", "Networker"]
    },
    {
        "name": "Real Estate Investor",
        "age_range": "30-45",
        "profession": "Property Developer",
        "region": "Miami",
        "interests": ["RealEstate", "Finance", "Business", "Travel"],
        "behaviors": ["Long-Term-Thinker", "Market-Analyst", "Portfolio-Builder"]
    },
    {
        "name": "Political Analyst",
        "age_range": "35-50",
        "profession": "Political Consultant",
        "region": "Washington D.C.",
        "interests": ["Politics", "History", "Business", "Academic"],
        "behaviors": ["Debate-Ready", "Policy-Savvy", "Networker"]
    },
    {
        "name": "News Junkie",
        "age_range": "40-55",
        "profession": "Journalist",
        "region": "New York",
        "interests": ["Entertainment", "Politics", "Finance", "Technology"],
        "behaviors": ["Information-Hungry", "Critical-Thinker", "Current-Aware"]
    },
    {
        "name": "Minimalist Lifestyle Blogger",
        "age_range": "28-38",
        "profession": "Lifestyle Influencer",
        "region": "Portland",
        "interests": ["Environment", "Wellness", "Medical", "Home"],
        "behaviors": ["Sustainability-Focused", "Intentional", "Mindful"]
    },
    {
        "name": "DIY Home Renovation Enthusiast",
        "age_range": "35-50",
        "profession": "Contractor",
        "region": "Denver",
        "interests": ["Home", "Automotive", "Sports", "Outdoor"],
        "behaviors": ["Hands-On", "Resourceful", "Cost-Conscious"]
    },
    {
        "name": "Classic Car Collector",
        "age_range": "45-60",
        "profession": "Auto Mechanic",
        "region": "Florida",
        "interests": ["Automotive", "Travel", "History", "Business"],
        "behaviors": ["Detail-Oriented", "Collector", "Heritage-Valuing"]
    },
    {
        "name": "Portrait Photographer",
        "age_range": "28-40",
        "profession": "Freelance Photographer",
        "region": "New York",
        "interests": ["Crafts", "Fashion", "Travel", "Beauty"],
        "behaviors": ["Visual-Artist", "Patient", "Storyteller"]
    },
    {
        "name": "CrossFit Enthusiast",
        "age_range": "25-35",
        "profession": "Personal Trainer",
        "region": "Los Angeles",
        "interests": ["Fitness", "Wellness", "Gaming", "Sports"],
        "behaviors": ["High-Energy", "Community-Oriented", "Goal-Crusher"]
    },
    {
        "name": "Beauty Guru & Skincare Expert",
        "age_range": "22-32",
        "profession": "Beauty YouTuber",
        "region": "Los Angeles",
        "interests": ["Beauty", "Fashion", "Wellness", "Entertainment"],
        "behaviors": ["Trend-Following", "Self-Care-Focused", "Brand-Loyal"]
    },
    {
        "name": "New Dad Navigating Parenthood",
        "age_range": "30-40",
        "profession": "Product Manager",
        "region": "Seattle",
        "interests": ["Parenting", "Technology", "Sports", "Medical"],
        "behaviors": ["Research-Heavy", "Practical", "Time-Constrained"]
    },
    {
        "name": "Dog Trainer & Pet Influencer",
        "age_range": "25-35",
        "profession": "Pet Care Specialist",
        "region": "San Diego",
        "interests": ["Pets", "Travel", "Crafts", "Outdoor"],
        "behaviors": ["Animal-Lover", "Patient", "Community-Builder"]
    },
    {
        "name": "Climate Activist",
        "age_range": "22-32",
        "profession": "Environmental Consultant",
        "region": "Portland",
        "interests": ["Environment", "Politics", "Science", "Agriculture"],
        "behaviors": ["Cause-Driven", "Advocacy-Focused", "Sustainable-Living"]
    },
    {
        "name": "Wedding Planner",
        "age_range": "28-40",
        "profession": "Event Coordinator",
        "region": "New York",
        "interests": ["Relationships", "Fashion", "Travel", "Entertainment"],
        "behaviors": ["Detail-Oriented", "Multi-Tasker", "Client-Focused"]
    },
    {
        "name": "Craft Beer Enthusiast",
        "age_range": "30-45",
        "profession": "Brewery Owner",
        "region": "Portland",
        "interests": ["Food", "Cooking", "Travel", "Outdoors"],
        "behaviors": ["Social-Drinker", "Quality-Seeker", "Local-Supporter"]
    },
    {
        "name": "Military Veteran Advocate",
        "age_range": "35-50",
        "profession": "Veterans Affairs Coordinator",
        "region": "San Antonio",
        "interests": ["Military", "Politics", "Sports", "History"],
        "behaviors": ["Disciplined", "Service-Minded", "Community-Supporter"]
    },
    {
        "name": "Retirement Planning Specialist",
        "age_range": "45-55",
        "profession": "Financial Advisor",
        "region": "Phoenix",
        "interests": ["Retirement", "Finance", "Travel", "Golf"],
        "behaviors": ["Client-Focused", "Regulatory-Minded", "Trust-Builder"]
    },
    {
        "name": "Immigration Attorney",
        "age_range": "32-45",
        "profession": "Lawyer",
        "region": "Houston",
        "interests": ["Legal", "Politics", "History", "Relationships"],
        "behaviors": ["Detail-Oriented", "Advocate", "Multilingual"]
    }
]

# 40 hours in milliseconds
ROTATION_INTERVAL_MS = 40 * 60 * 60 * 1000

# Persistence file for last persona
DATA_DIR = os.environ.get("DATA_DIR", "/data")
LAST_PERSONA_FILE = os.path.join(DATA_DIR, "last_persona.json")


def _get_category_pool(name: str) -> CategoryPool:
    """Convert string category name to CategoryPool enum."""
    mapping = {
        "technology": CategoryPool.TECHNOLOGY,
        "finance": CategoryPool.FINANCE,
        "travel": CategoryPool.TRAVEL,
        "food": CategoryPool.FOOD,
        "gaming": CategoryPool.GAMING,
        "fashion": CategoryPool.FASHION,
        "sports": CategoryPool.SPORTS,
        "music": CategoryPool.MUSIC,
        "cooking": CategoryPool.COOKING,
        "automotive": CategoryPool.AUTOMOTIVE,
        "parenting": CategoryPool.PARENTING,
        "pets": CategoryPool.PETS,
        "environment": CategoryPool.ENVIRONMENT,
        "science": CategoryPool.SCIENCE,
        "business": CategoryPool.BUSINESS,
        "politics": CategoryPool.POLITICS,
        "beauty": CategoryPool.BEAUTY,
        "fitness": CategoryPool.FITNESS,
        "entertainment": CategoryPool.ENTERTAINMENT,
        "home": CategoryPool.HOME_IMPROVEMENT,
        "crafts": CategoryPool.CRAFTS,
        "history": CategoryPool.HISTORY,
        "academic": CategoryPool.ACADEMIC,
        "outdoor": CategoryPool.OUTDOOR_RECREATION,
        "realestate": CategoryPool.REAL_ESTATE,
        "relationships": CategoryPool.RELATIONSHIPS_DATING,
        "wellness": CategoryPool.WELLNESS_ALTERNATIVE,
        "agriculture": CategoryPool.AGRICULTURE,
        "military": CategoryPool.MILITARY_DEFENSE,
        "retirement": CategoryPool.RETIREMENT,
        "legal": CategoryPool.LEGAL,
        "medical": CategoryPool.MEDICAL,
    }
    key = name.lower().replace("_", "").replace(" ", "").replace("-", "")
    return mapping.get(key)


def get_persona_from_pool(exclude_name: str = None) -> dict:
    """Get a random persona from the pool, excluding the given name."""
    available = [p for p in PERSONA_POOL if p["name"] != exclude_name]
    return random.choice(available) if available else random.choice(PERSONA_POOL)


def save_last_persona(persona: dict):
    """Save last persona to disk for persistence across restarts."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LAST_PERSONA_FILE, "w") as f:
            json.dump(persona, f)
    except Exception as e:
        print(f"Warning: Could not save persona: {e}")


def load_last_persona() -> Optional[dict]:
    """Load last persona from disk."""
    try:
        if os.path.exists(LAST_PERSONA_FILE):
            with open(LAST_PERSONA_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load persona: {e}")
    return None


@dataclass
class SyntheticPersona:
    """A synthetic identity for noise generation."""
    id: str
    name: str
    age_range: str
    profession: str
    region: str
    interests: Set[CategoryPool]
    behaviors: list
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
        active_hours: int = 40,
        behaviors: list = None,
    ) -> "SyntheticPersona":
        now = int(time.time() * 1000)
        jitter = random.randint(1, 4) * 60 * 60 * 1000  # 1-4 hours jitter
        active_until = now + (active_hours * 60 * 60 * 1000) + jitter
        
        return cls(
            id=f"persona_{now}",
            name=name,
            age_range=age_range,
            profession=profession,
            region=region,
            interests=interests,
            behaviors=behaviors or [],
            created_at=now,
            active_until=active_until,
        )

    @classmethod
    def from_pool(cls, persona_data: dict) -> "SyntheticPersona":
        """Create SyntheticPersona from pool data."""
        interests = set()
        for interest_str in persona_data.get("interests", []):
            cat = _get_category_pool(interest_str)
            if cat:
                interests.add(cat)
        
        return cls.create(
            name=persona_data["name"],
            age_range=persona_data["age_range"],
            profession=persona_data["profession"],
            region=persona_data["region"],
            interests=interests,
            behaviors=persona_data.get("behaviors", []),
        )


class PersonaRotationLayer:
    """
    Layer 3: Synthetic Persona Rotation
    Rotates persona every ~40 hours using pre-defined pool.
    """
    
    ALIGNED_WEIGHT = 2.0
    MISALIGNED_WEIGHT = 0.3
    NEUTRAL_WEIGHT = 1.0
    PERSONA_FOLLOW_FRACTION = 0.70
    
    def __init__(self, persona: SyntheticPersona = None, exclude_last: str = None):
        if persona is None:
            last_persona = load_last_persona()
            if last_persona and last_persona.get("name") != exclude_last:
                persona = SyntheticPersona.from_pool(last_persona)
            else:
                pool_persona = get_persona_from_pool(exclude_name=exclude_last)
                persona = SyntheticPersona.from_pool(pool_persona)
                save_last_persona(pool_persona)
        
        self._persona = persona
        self._enabled = True
        self._weights = {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
        self._recompute_weights()
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def get_weights(self) -> dict[CategoryPool, float]:
        if not self._enabled:
            return {cat: self.NEUTRAL_WEIGHT for cat in CategoryPool}
        return dict(self._weights)
    
    def get_current_persona(self) -> Optional[SyntheticPersona]:
        """Get the current active persona."""
        return self._persona
    
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
        """Check if current persona has expired (40 hours)."""
        if not self._persona:
            return True
        now = int(time.time() * 1000)
        return now >= self._persona.active_until
    
    def rotate_to_next(self) -> SyntheticPersona:
        """Rotate to next persona in pool (different from current)."""
        pool_persona = get_persona_from_pool(exclude_name=self._persona.name)
        new_persona = SyntheticPersona.from_pool(pool_persona)
        save_last_persona(pool_persona)
        self.set_persona(new_persona)
        return new_persona
    
    def check_and_rotate(self) -> Optional[SyntheticPersona]:
        """Check if rotation needed and perform it."""
        if self.is_expired():
            return self.rotate_to_next()
        return None


class PersonaGenerator:
    """
    Generates synthetic personas from pre-defined pool.
    """
    
    MAX_ATTEMPTS = 10
    
    def __init__(self, templates: list = None):
        self.templates = templates or PERSONA_POOL
    
    def generate(self, exclude_name: str = None) -> SyntheticPersona:
        """Generate a new synthetic persona from pool."""
        pool_persona = get_persona_from_pool(exclude_name=exclude_name)
        return SyntheticPersona.from_pool(pool_persona)
    
    @staticmethod
    def next_rotation_time() -> int:
        """Calculate next rotation timestamp (40 hours + jitter)."""
        jitter = random.randint(1, 4) * 60 * 60 * 1000  # 1-4 hours
        now = int(time.time() * 1000)
        return now + ROTATION_INTERVAL_MS + jitter
