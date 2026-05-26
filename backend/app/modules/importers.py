import json
import zipfile
import io
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from app.models.enums import CategoryPool


@dataclass
class ImportResult:
    success: bool
    message: str
    categories_found: int = 0


class CategoryMapper:
    """
    Maps platform-specific interest strings to CategoryPool.
    """
    
    def __init__(self, assets_path: str = None):
        self.assets_path = Path(assets_path) if assets_path else None
        self.exact_map = {}
        self.fuzzy_map = {}
        self._load_map()
    
    def _load_map(self):
        """Load platform_category_map.json from assets."""
        if not self.assets_path:
            self._init_heuristics()
            return
        
        paths = [
            self.assets_path / "platform_category_map.json",
            self.assets_path.parent / "platform_category_map.json",
        ]
        
        for path in paths:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.exact_map = data
                break
        
        if not self.exact_map:
            self._init_heuristics()
    
    def _init_heuristics(self):
        """Fallback heuristics when no map file."""
        self.fuzzy_map = {
            "technology": CategoryPool.TECHNOLOGY,
            "tech": CategoryPool.TECHNOLOGY,
            "gaming": CategoryPool.GAMING,
            "games": CategoryPool.GAMING,
            "sports": CategoryPool.SPORTS,
            "fitness": CategoryPool.FITNESS,
            "health": CategoryPool.MEDICAL,
            "medical": CategoryPool.MEDICAL,
            "finance": CategoryPool.FINANCE,
            "business": CategoryPool.BUSINESS,
            "travel": CategoryPool.TRAVEL,
            "food": CategoryPool.FOOD,
            "cooking": CategoryPool.COOKING,
            "music": CategoryPool.MUSIC,
            "fashion": CategoryPool.FASHION,
            "beauty": CategoryPool.BEAUTY,
            "pets": CategoryPool.PETS,
            "science": CategoryPool.SCIENCE,
            "politics": CategoryPool.POLITICS,
            "environment": CategoryPool.ENVIRONMENT,
        }
    
    def map(self, platform_string: str) -> Optional[CategoryPool]:
        """Map a platform string to CategoryPool."""
        if not platform_string:
            return None
        
        s = platform_string.lower().strip()
        
        # Exact match
        if s in self.exact_map:
            cat_str = self.exact_map[s]
            try:
                return CategoryPool[cat_str.upper()]
            except KeyError:
                pass
        
        # Fuzzy match via heuristics
        for keyword, cat in self.fuzzy_map.items():
            if keyword in s:
                return cat
        
        return None
    
    def map_all(self, strings: list[str]) -> set[CategoryPool]:
        """Map multiple strings to categories."""
        result = set()
        for s in strings:
            cat = self.map(s)
            if cat:
                result.add(cat)
        return result


class GoogleTakeoutImporter:
    """
    Imports Google Ads profile from Takeout export.
    Supports MyAdCenter.json and MyActivity Ads format.
    """
    
    def __init__(self, category_mapper: CategoryMapper):
        self.category_mapper = category_mapper
    
    async def import_profile(self, file_content: bytes, filename: str) -> ImportResult:
        """Import Google Takeout profile from ZIP or JSON."""
        try:
            # Check if ZIP
            if filename.endswith('.zip') or zipfile.is_zipfile(io.BytesIO(file_content)):
                categories = await self._extract_from_zip(file_content)
            else:
                # Direct JSON
                categories = self._extract_from_json(file_content.decode('utf-8'))
            
            if not categories:
                return ImportResult(
                    success=False,
                    message="No categories found in Google Takeout export"
                )
            
            # Map to CategoryPool
            mapped = self.category_mapper.map_all(categories)
            
            return ImportResult(
                success=True,
                message=f"Imported {len(mapped)} categories from Google",
                categories_found=len(mapped)
            )
        
        except Exception as e:
            return ImportResult(
                success=False,
                message=f"Import failed: {str(e)}"
            )
    
    async def _extract_from_zip(self, content: bytes) -> list[str]:
        """Extract categories from ZIP archive."""
        categories = []
        
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Priority: MyAdCenter.json first, then MyActivity Ads
            names = zf.namelist()
            
            my_adcenter = [n for n in names if 'MyAdCenter' in n or 'adcenter' in n.lower()]
            my_activity = [n for n in names if 'MyActivity' in n and 'ads' in n.lower()]
            
            if my_adcenter:
                with zf.open(my_adcenter[0]) as f:
                    data = json.load(f)
                    categories.extend(self._parse_my_adcenter(data))
            
            if my_activity and not my_adcenter:
                for name in my_activity:
                    with zf.open(name) as f:
                        data = json.load(f)
                        categories.extend(self._parse_my_activity_ads(data))
        
        return list(set(categories))
    
    def _extract_from_json(self, content: str) -> list[str]:
        """Extract categories from JSON."""
        try:
            data = json.loads(content)
            
            # Try MyAdCenter format
            if isinstance(data, dict):
                if 'interests' in data:
                    return data['interests']
                if 'advertisingTopics' in data:
                    return [t.get('name', '') for t in data['advertisingTopics']]
            
            # Try MyActivity format
            if isinstance(data, list):
                categories = []
                for item in data:
                    if isinstance(item, dict):
                        details = item.get('details', [])
                        for d in details:
                            if d.get('name') == 'Ad Targeting':
                                categories.append(d.get('title', ''))
                return categories
        
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _parse_my_adcenter(self, data: dict) -> list[str]:
        """Parse MyAdCenter format."""
        categories = []
        
        if 'interests' in data:
            categories.extend(data['interests'])
        
        if 'advertisingTopics' in data:
            for topic in data['advertisingTopics']:
                if isinstance(topic, dict):
                    categories.append(topic.get('name', ''))
                elif isinstance(topic, str):
                    categories.append(topic)
        
        return [c for c in categories if c]
    
    def _parse_my_activity_ads(self, data: list) -> list[str]:
        """Parse MyActivity Ads format."""
        categories = []
        
        for item in data:
            if isinstance(item, dict):
                details = item.get('details', [])
                for d in details:
                    if isinstance(d, dict) and d.get('name') == 'Ad Targeting':
                        title = d.get('title', '')
                        if title:
                            categories.append(title)
        
        return categories


class FacebookDyiImporter:
    """
    Imports Facebook advertising profile from "Download Your Information" export.
    """
    
    def __init__(self, category_mapper: CategoryMapper):
        self.category_mapper = category_mapper
    
    async def import_profile(self, file_content: bytes, filename: str) -> ImportResult:
        """Import Facebook DYI profile from ZIP or JSON."""
        try:
            if filename.endswith('.zip') or zipfile.is_zipfile(io.BytesIO(file_content)):
                categories = await self._extract_from_zip(file_content)
            else:
                categories = self._extract_from_json(file_content.decode('utf-8'))
            
            if not categories:
                return ImportResult(
                    success=False,
                    message="No categories found in Facebook export"
                )
            
            mapped = self.category_mapper.map_all(categories)
            
            return ImportResult(
                success=True,
                message=f"Imported {len(mapped)} categories from Facebook",
                categories_found=len(mapped)
            )
        
        except Exception as e:
            return ImportResult(
                success=False,
                message=f"Import failed: {str(e)}"
            )
    
    async def _extract_from_zip(self, content: bytes) -> list[str]:
        """Extract categories from ZIP archive."""
        categories = []
        
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()
            
            # Priority: 2024 format first
            other_categories = [n for n in names if 'other_categories_used_to_reach_you' in n]
            ads_interests = [n for n in names if 'ads_interests' in n.lower()]
            
            if other_categories:
                with zf.open(other_categories[0]) as f:
                    data = json.load(f)
                    categories.extend(self._parse_label_values(data))
            
            elif ads_interests:
                with zf.open(ads_interests[0]) as f:
                    data = json.load(f)
                    categories.extend(self._parse_ads_interests(data))
        
        return list(set(categories))
    
    def _extract_from_json(self, content: str) -> list[str]:
        """Extract categories from JSON."""
        try:
            data = json.loads(content)
            return self._parse_ads_interests(data)
        except json.JSONDecodeError:
            return []
    
    def _parse_label_values(self, data: dict) -> list[str]:
        """Parse 2024 format with label_values structure."""
        categories = []
        
        if isinstance(data, dict) and 'label_values' in data:
            for lv in data['label_values']:
                if isinstance(lv, dict) and 'vec' in lv:
                    for item in lv['vec']:
                        if isinstance(item, dict):
                            val = item.get('value', '')
                            if val:
                                categories.append(val)
        
        return categories
    
    def _parse_ads_interests(self, data) -> list[str]:
        """Parse various ads_interests formats."""
        categories = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    categories.append(item)
                elif isinstance(item, dict):
                    if 'topic' in item:
                        categories.append(item['topic'])
                    elif 'name' in item:
                        categories.append(item['name'])
                    elif 'topics_v2' in item:
                        categories.extend(item['topics_v2'])
        
        elif isinstance(data, dict):
            if 'topics_v2' in data:
                categories.extend(data['topics_v2'])
            if 'ads_interests' in data:
                categories.extend(data['ads_interests'])
        
        return [c for c in categories if c]
