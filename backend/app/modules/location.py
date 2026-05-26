import random
import json
from pathlib import Path
from dataclasses import dataclass
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


@dataclass
class CityCoord:
    name: str
    lat: float
    lng: float
    region: str = ""


class LocationSpoofModule(Module):
    """
    Spoofs GPS location via VPN/proxy rotation.
    On Docker, instead of MockLocationProvider, we rotate
    through VPN endpoints or proxy servers.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.cities = []
        self._enabled = True
        self.current_location = None
        self._load_cities()
    
    def _load_cities(self):
        """Load city coordinates from assets."""
        if not self.assets_path:
            # Fallback sample cities
            self.cities = [
                CityCoord("New York", 40.7128, -74.0060, "US"),
                CityCoord("Los Angeles", 34.0522, -118.2437, "US"),
                CityCoord("London", 51.5074, -0.1278, "UK"),
                CityCoord("Paris", 48.8566, 2.3522, "FR"),
                CityCoord("Tokyo", 35.6762, 139.6503, "JP"),
            ]
            return
        
        paths = [
            self.assets_path / "city_coords.json",
            self.assets_path.parent / "city_coords.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.cities = [
                            CityCoord(**c) if isinstance(c, dict) else c
                            for c in data
                        ]
                break
        
        if not self.cities:
            self.cities = [CityCoord("Unknown", 0.0, 0.0, "US")]
    
    async def start(self):
        self.current_location = self._random_city()
    
    async def stop(self):
        pass
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def _random_city(self, region_hint: str = None) -> CityCoord:
        if not self.cities:
            return CityCoord("Unknown", 0.0, 0.0, "US")
        
        if region_hint:
            region_cities = [c for c in self.cities if c.region == region_hint]
            if region_cities:
                return random.choice(region_cities)
        
        return random.choice(self.cities)
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        # Rotate to new location
        self.current_location = self._random_city()
        city = self.current_location
        
        # In a real implementation, this would:
        # 1. Connect to a VPN endpoint in the target region
        # 2. Or rotate to a proxy server in that region
        # For now, we just log the "intended" location
        
        return ActionLogEntry(
            action_type=ActionType.LOCATION_SPOOF,
            category=category,
            detail=f"Location: {city.name} ({city.lat:.4f}, {city.lng:.4f})",
            success=True,
        )
