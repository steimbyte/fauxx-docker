import asyncio
import random
import json
from pathlib import Path
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


class DnsNoiseModule(Module):
    """
    Generates DNS query noise for network-level confusion.
    Uses crawl URL corpus to pick random domains.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.domains = []
        self._enabled = True
        self._load_domains()
    
    def _load_domains(self):
        """Load domains from crawl_urls.json."""
        if not self.assets_path:
            # Fallback sample domains
            self.domains = [
                "example.com", "test.com", "demo.org",
                "google.com", "facebook.com", "amazon.com",
            ]
            return
        
        paths = [
            self.assets_path / "crawl_urls.json",
            self.assets_path.parent / "crawl_urls.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.domains = [entry.get("domain") or entry.get("url", "").split("/")[2] 
                                       for entry in data if entry]
                    elif isinstance(data, dict):
                        self.domains = list(data.keys())
                break
        
        if not self.domains:
            self.domains = ["example.com", "test.com", "demo.org"]
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        if not self.domains:
            self._load_domains()
        
        domain = random.choice(self.domains)
        
        try:
            # Perform DNS lookup using asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, __import__("socket").gethostbyname, domain)
            success = True
            detail = f"DNS: {domain}"
        except Exception as e:
            success = False
            detail = f"DNS error: {str(e)[:50]}"
        
        return ActionLogEntry(
            action_type=ActionType.DNS_LOOKUP,
            category=category,
            detail=detail,
            success=success,
        )
