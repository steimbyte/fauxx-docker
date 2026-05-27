import httpx
import asyncio
import random
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


AD_DASHBOARD_URLS = [
    "https://adssettings.google.com/",
    "https://optout.aboutads.info/",
    "https://www.networkadvertising.org/choices/",
]


class AdPollutionModule(Module):
    """
    Visits ad-heavy pages and clicks ads to pollute ad profiles.
    Uses httpx for HTTP requests (WebView equivalent in Docker).
    """
    
    def __init__(self):
        self._enabled = True
        self._client = None
        self.crawl_urls = []  # TODO: load from CrawlListManager
    
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
        
        # 10% chance: visit ad dashboard
        if random.random() < 0.1:
            url = random.choice(AD_DASHBOARD_URLS)
            action_type = ActionType.AD_CLICK
        else:
            # 90% chance: visit crawl URL
            # TODO: use CrawlListManager for category-weighted URLs
            url = self._get_random_crawl_url(category)
            action_type = ActionType.PAGE_VISIT
        
        try:
            response = await self._client.get(url)
            success = response.status_code == 200
            detail = f"{action_type.value}: {url[:50]}..."
            # Simulate dwell time
            await asyncio.sleep(random.uniform(3, 15))
        except Exception as e:
            success = False
            detail = f"Error: {str(e)[:50]}"
        
        return ActionLogEntry(
            action_type=action_type,
            category=category,
            detail=detail,
            success=success,
        )
    
    def _get_random_crawl_url(self, category: CategoryPool) -> str:
        # Real, accessible domains for ad impression simulation
        fallbacks = [
            "https://www.google.com",
            "https://www.bing.com",
            "https://www.wikipedia.org",
            "https://news.ycombinator.com",
            "https://www.github.com",
            "https://www.reddit.com",
        ]
        return random.choice(fallbacks)
