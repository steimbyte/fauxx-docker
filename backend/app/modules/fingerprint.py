import random
import json
from pathlib import Path
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


class FingerprintModule(Module):
    """
    Rotates User-Agent and browser fingerprints.
    On Docker this sets headers for HTTP requests.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.user_agents = []
        self.current_ua = None
        self._enabled = True
        self._load_user_agents()
    
    def _load_user_agents(self):
        """Load user agents from assets."""
        if not self.assets_path:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            ]
            return
        
        paths = [
            self.assets_path / "user_agents.json",
            self.assets_path.parent / "user_agents.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.user_agents = data
                    elif isinstance(data, dict) and "agents" in data:
                        self.user_agents = data["agents"]
                break
        
        if not self.user_agents:
            self.user_agents = ["Mozilla/5.0 (compatible; FauxxBot/1.0)"]
    
    async def start(self):
        self.current_ua = self.random_ua()
    
    async def stop(self):
        pass
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def random_ua(self) -> str:
        return random.choice(self.user_agents)
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        old_ua = self.current_ua
        self.current_ua = self.random_ua()
        
        return ActionLogEntry(
            action_type=ActionType.FINGERPRINT_ROTATE,
            category=category,
            detail=f"UA: {self.current_ua[:40]}...",
            success=True,
        )
    
    def get_current_ua(self) -> str:
        return self.current_ua or self.user_agents[0] if self.user_agents else ""
