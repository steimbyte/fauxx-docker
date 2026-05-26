import json
import random
from pathlib import Path
from dataclasses import dataclass
from app.models.enums import CategoryPool


@dataclass
class CrawlEntry:
    url: str
    domain: str
    category: CategoryPool


@dataclass
class PendingCrawlEntry:
    entry: CrawlEntry
    wait_ms: int = 0


MIN_DOMAIN_INTERVAL_MS = 5000
STALE_ENTRY_THRESHOLD_MS = 24 * 60 * 60 * 1000


class CrawlListManager:
    """
    Manages URL corpus for cookie saturation and ad pollution.
    Category-weighted URL selection with rate limiting.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.urls_by_category = {cat: [] for cat in CategoryPool}
        self.last_visit = {}
        self._load_urls()
    
    def _load_urls(self):
        """Load crawl URLs from assets."""
        if not self.assets_path:
            self._load_fallback()
            return
        
        paths = [
            self.assets_path / "crawl_urls.json",
            self.assets_path / "crawl_urls" / "en.json",
            self.assets_path.parent / "crawl_urls.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    self._parse_urls(data)
                break
        
        if not any(self.urls_by_category.values()):
            self._load_fallback()
    
    def _load_fallback(self):
        """Load fallback URLs when assets unavailable."""
        # Simple fallback URLs
        fallbacks = [
            "https://www.wikipedia.org",
            "https://www.example.com",
            "https://www.github.com",
            "https://www.stackoverflow.com",
            "https://www.reddit.com",
        ]
        for cat in CategoryPool:
            self.urls_by_category[cat] = [
                CrawlEntry(url=f"{url}/{cat.value.lower()}", domain=url.split("/")[2], category=cat)
                for url in fallbacks
            ]
    
    def _parse_urls(self, data):
        """Parse crawl URL data."""
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    url = entry.get("url", "")
                    cat_str = entry.get("category", "")
                    try:
                        cat = CategoryPool[cat_str.upper()]
                    except (KeyError, AttributeError):
                        cat = CategoryPool.ENTERTAINMENT
                    
                    domain = self._extract_domain(url)
                    self.urls_by_category[cat].append(CrawlEntry(url=url, domain=domain, category=cat))
        elif isinstance(data, dict):
            for cat_str, urls in data.items():
                try:
                    cat = CategoryPool[cat_str.upper()]
                except (KeyError, AttributeError):
                    continue
                
                for url in urls:
                    if isinstance(url, str):
                        domain = self._extract_domain(url)
                        self.urls_by_category[cat].append(CrawlEntry(url=url, domain=domain, category=cat))
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        if "//" in url:
            return url.split("/")[2]
        return url.split("/")[0]
    
    def corpus_size(self) -> int:
        """Total number of URLs in corpus."""
        return sum(len(urls) for urls in self.urls_by_category.values())
    
    def next_url(self, category: CategoryPool = None) -> CrawlEntry | None:
        """Get next URL, optionally filtered by category."""
        if category:
            urls = self.urls_by_category.get(category, [])
            if urls:
                return random.choice(urls)
            return None
        
        # Random from all categories
        all_entries = []
        for urls in self.urls_by_category.values():
            all_entries.extend(urls)
        
        return random.choice(all_entries) if all_entries else None
    
    def next_url_or_wait(self, category: CategoryPool = None) -> PendingCrawlEntry:
        """Get next URL with wait time if rate limited."""
        entry = self.next_url(category)
        
        if not entry:
            return PendingCrawlEntry(entry=None, wait_ms=0)
        
        now = int(__import__("time").time() * 1000)
        last = self.last_visit.get(entry.domain, 0)
        elapsed = now - last
        
        if elapsed < MIN_DOMAIN_INTERVAL_MS:
            return PendingCrawlEntry(
                entry=entry,
                wait_ms=MIN_DOMAIN_INTERVAL_MS - elapsed
            )
        
        return PendingCrawlEntry(entry=entry, wait_ms=0)
    
    def mark_visited(self, domain: str, timestamp: int = None):
        """Mark domain as visited."""
        self.last_visit[domain] = timestamp or int(__import__("time").time() * 1000)
        
        # Cleanup stale entries
        self._cleanup_stale()
    
    def is_eligible(self, domain: str, now: int = None) -> bool:
        """Check if domain is eligible (not rate limited)."""
        now = now or int(__import__("time").time() * 1000)
        last = self.last_visit.get(domain, 0)
        return (now - last) >= MIN_DOMAIN_INTERVAL_MS
    
    def _cleanup_stale(self):
        """Remove stale visit entries."""
        now = int(__import__("time").time() * 1000)
        stale_keys = [
            domain for domain, timestamp in self.last_visit.items()
            if (now - timestamp) > STALE_ENTRY_THRESHOLD_MS
        ]
        for domain in stale_keys:
            del self.last_visit[domain]


class DomainBlocklist:
    """
    Checks if domains/URLs should be blocked.
    Fail-closed: blocks all if load fails.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.exact_domains = set()
        self.subdomain_domains = set()
        self.regexes = []
        self.load_failed = False
        self._load_blocklist()
    
    def _load_blocklist(self):
        """Load blocklist from assets."""
        if not self.assets_path:
            self.load_failed = True
            return
        
        paths = [
            self.assets_path / "blocklist.json",
            self.assets_path.parent / "blocklist.json",
        ]
        
        for path in paths:
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                        self._parse_blocklist(data)
                    self.load_failed = False
                    return
                except Exception:
                    self.load_failed = True
                    return
        
        self.load_failed = True
    
    def _parse_blocklist(self, data):
        """Parse blocklist JSON."""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    self.exact_domains.add(item.lower())
                elif isinstance(item, dict):
                    domain = item.get("domain", "")
                    if domain:
                        self.exact_domains.add(domain.lower())
        elif isinstance(data, dict):
            if "domains" in data:
                for domain in data["domains"]:
                    self.exact_domains.add(domain.lower())
    
    def is_blocked(self, host: str) -> bool:
        """Check if domain is blocked."""
        if self.load_failed:
            return True  # Fail closed
        
        host_lower = host.lower()
        
        # Exact match
        if host_lower in self.exact_domains:
            return True
        
        # Subdomain match
        for blocked in self.subdomain_domains:
            if host_lower.endswith(blocked):
                return True
        
        # Regex match
        for regex in self.regexes:
            if regex.search(host_lower):
                return True
        
        return False
    
    def is_url_blocked(self, url: str) -> bool:
        """Check if URL is blocked."""
        if "//" in url:
            domain = url.split("/")[2]
        else:
            domain = url
        
        return self.is_blocked(domain)
