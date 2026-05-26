import httpx
import random
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


# Multi-locale Play Store search keywords
PLAY_KEYWORDS = {
    "MEDICAL": ["health", "medicine", "wellness", "fitness"],
    "FINANCE": ["banking", "investment", "crypto", "trading"],
    "GAMING": ["games", "arcade", "rpg", "action"],
    "TRAVEL": ["hotels", "flights", "booking", "vacation"],
    "SHOPPING": ["shopping", "deals", "discounts", "products"],
}


class AppSignalModule(Module):
    """
    Simulates mobile app signals by visiting app store pages.
    This creates signals that ad networks interpret as app interest.
    """
    
    def __init__(self):
        self._enabled = False  # Disabled by default like Fauxx
        self._client = None
    
    async def start(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        )
    
    async def stop(self):
        if self._client:
            await self._client.aclose()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        if not self._client:
            await self.start()
        
        # Build Play Store URL with category keywords
        keywords = PLAY_KEYWORDS.get(category.value, ["apps", "software"])
        keyword = random.choice(keywords)
        
        url = f"https://play.google.com/store/search?q={keyword}&c=apps&hl=en"
        
        try:
            response = await self._client.get(url)
            success = response.status_code == 200
            detail = f"DeepLink: {url[:50]}..."
        except Exception as e:
            success = False
            detail = f"Error: {str(e)[:50]}"
        
        return ActionLogEntry(
            action_type=ActionType.DEEP_LINK_VISIT,
            category=category,
            detail=detail,
            success=success,
        )
