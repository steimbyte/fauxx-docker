import httpx
import asyncio
import random
import json
from pathlib import Path
from collections import defaultdict
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType


class MarkovQueryGenerator:
    """
    Generates natural-sounding search queries using Markov chains.
    """
    
    def __init__(self, query_banks_path: Path = None):
        self.query_banks_path = query_banks_path
        self.bigram_map = defaultdict(list)
        self.trained_categories = set()
        self.seed_phrases = defaultdict(list)
        
        self.SEED_PHRASE_PROBABILITY = 0.3
        self.MAX_SEED_WORDS = 6
        self.MIN_PLAUSIBLE_WORDS = 3
        self.MAX_RESAMPLE_ATTEMPTS = 5
    
    def load_queries(self, category: CategoryPool, locale: str = "en"):
        """Load query corpus for category and train bigram model."""
        if not self.query_banks_path or category in self.trained_categories:
            return
        
        # Try locale-specific file first, then fallback
        paths = [
            self.query_banks_path / locale / f"{category.value}.json",
            self.query_banks_path / f"{category.value}.json",
            self.query_banks_path.parent / "query_banks" / locale / f"{category.value}.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    queries = json.load(f)
                self._train(queries)
                self.trained_categories.add(category)
                break
    
    def _train(self, queries: list[str]):
        """Build bigram model from query corpus."""
        self.bigram_map.clear()
        for query in queries:
            words = query.lower().split()
            if len(words) < 2:
                continue
            for i in range(len(words) - 1):
                self.bigram_map[words[i]].append(words[i + 1])
    
    def generate(self, category: CategoryPool, target_length: int = None) -> str:
        """Generate a query using bigram model."""
        target_length = target_length or random.randint(3, 9)
        
        # Try seed phrase first
        if self.seed_phrases.get(category) and random.random() < self.SEED_PHRASE_PROBABILITY:
            seed = random.choice(self.seed_phrases[category])
            result = seed.lower().split()
        else:
            # Start from random word
            if not self.bigram_map:
                return self._safe_fallback(category)
            start_word = random.choice(list(self.bigram_map.keys()))
            result = [start_word]
        
        # Generate continuation
        for _ in range(target_length):
            last = result[-1]
            if last not in self.bigram_map:
                break
            next_words = self.bigram_map[last]
            result.append(random.choice(next_words))
        
        if len(result) < self.MIN_PLAUSIBLE_WORDS:
            return self._safe_fallback(category)
        
        return " ".join(result)
    
    def inject_seed_phrases(self, category: CategoryPool, phrases: list[str]):
        """Add seed phrases for more targeted queries."""
        self.seed_phrases[category].extend(phrases)
    
    def _safe_fallback(self, category: CategoryPool) -> str:
        """Fallback query when generation fails."""
        fallbacks = [
            f"best {category.value.lower()} tips",
            f"how to choose {category.value.lower()}",
            f"top rated {category.value.lower()} reviews",
        ]
        return random.choice(fallbacks)


class SearchEngine:
    """Search engine URL builder."""
    
    def __init__(self, name: str, url_template: str):
        self.name = name
        self.url_template = url_template
    
    def build_url(self, query: str, locale: str = "en", region: str = "US") -> str:
        return self.url_template.format(
            q=query.replace(" ", "+"),
            locale=locale,
            region=region,
        )


SEARCH_ENGINES = [
    SearchEngine(
        "google",
        "https://www.google.com/search?q={q}&hl={locale}&gl={region}"
    ),
    SearchEngine(
        "bing",
        "https://www.bing.com/search?q={q}&setmkt={locale}-{region}"
    ),
    SearchEngine(
        "duckduckgo",
        "https://duckduckgo.com/?q={q}&kl={locale}-{region}"
    ),
    SearchEngine(
        "yahoo",
        "https://search.yahoo.com/search?p={q}"
    ),
    SearchEngine(
        "yandex",
        "https://yandex.com/search/?text={q}&lang={locale}"
    ),
]


class SearchPoisonModule(Module):
    """
    Executes synthetic search queries across multiple search engines.
    Uses Markov chain for natural-sounding queries.
    """
    
    def __init__(
        self,
        assets_path: str = None,
        locale: str = "en",
        region: str = "US",
    ):
        self.assets_path = Path(assets_path) if assets_path else None
        self.locale = locale
        self.region = region
        self.query_generator = MarkovQueryGenerator(self.assets_path)
        self._enabled = True
        self._client = None
    
    async def start(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FauxxBot/1.0)"}
        )
    
    async def stop(self):
        if self._client:
            await self._client.aclose()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        if not self._client:
            await self.start()
        
        # Ensure queries are loaded
        self.query_generator.load_queries(category, self.locale)
        
        # Generate query (60% Markov, 40% direct)
        if random.random() < 0.6:
            query = self.query_generator.generate(category)
        else:
            query = self.query_generator._safe_fallback(category)
        
        # Pick random search engine
        engine = random.choice(SEARCH_ENGINES)
        url = engine.build_url(query, self.locale, self.region)
        
        try:
            response = await self._client.get(url)
            success = response.status_code == 200
            detail = f"{engine.name}: {query[:50]}..."
        except Exception as e:
            success = False
            detail = f"Error: {str(e)[:100]}"
        
        return ActionLogEntry(
            action_type=ActionType.SEARCH_QUERY,
            category=category,
            detail=detail,
            success=success,
        )
