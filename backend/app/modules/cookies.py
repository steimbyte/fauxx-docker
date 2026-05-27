import httpx
import asyncio
import random
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


class CookieSaturationModule(Module):
    """
    Visits URLs to accumulate tracker cookies.
    Uses isolated sessions (equivalent to PhantomWebViewPool in Android).
    """
    
    def __init__(self):
        self._enabled = True
        self._client = None
        self.MIN_DOMAIN_INTERVAL_MS = 5000
        self.last_visit = {}
    
    async def start(self):
        # Create client with cookie jar
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            cookies=httpx.Cookies(),  # Persistent cookie jar
        )
    
    async def stop(self):
        if self._client:
            await self._client.aclose()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        if not self._client:
            await self.start()
        
        # TODO: use CrawlListManager for category-weighted URLs
        url = self._get_random_url(category)
        domain = url.split("/")[2] if "//" in url else url
        
        # Check rate limit
        if domain in self.last_visit:
            elapsed = asyncio.get_event_loop().time() * 1000 - self.last_visit[domain]
            if elapsed < self.MIN_DOMAIN_INTERVAL_MS:
                wait_ms = self.MIN_DOMAIN_INTERVAL_MS - elapsed
                await asyncio.sleep(wait_ms / 1000)
        
        try:
            response = await self._client.get(url)
            success = response.status_code == 200
            detail = f"Cookie: {url[:50]}..."
            
            # Update rate limit tracker
            self.last_visit[domain] = asyncio.get_event_loop().time() * 1000
            
            # Simulate dwell time (2-10s)
            await asyncio.sleep(random.uniform(2, 10))
        except Exception as e:
            success = False
            detail = f"Error: {str(e)[:50]}"
        
        return ActionLogEntry(
            action_type=ActionType.COOKIE_HARVEST,
            category=category,
            detail=detail,
            success=success,
        )
    
    def _get_random_url(self, category: CategoryPool) -> str:
        # Real, accessible domains for cookie harvesting simulation
        urls = [
            "https://www.google.com/search?q=test",
            "https://www.bing.com/search?q=test",
            "https://duckduckgo.com/?q=test",
            "https://news.ycombinator.com/",
            "https://www.wikipedia.org/",
            "https://www.reddit.com/",
            "https://www.amazon.com/s?k=test",
            "https://www.youtube.com/results?search_query=test",
            "https://twitter.com/search?q=test",
            "https://www.stackoverflow.com/search?q=test",
        ]
        return random.choice(urls)
