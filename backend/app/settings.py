import json
import os
from pathlib import Path

# Use /data for persistence in Docker, fallback to project data dir for dev
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
SETTINGS_FILE = Path(os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR))) / "settings.json"


class SettingsManager:
    _instance = None
    _settings = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                self._settings = json.load(f)
        else:
            self._settings = self._default_settings()
            self._save()
    
    def _default_settings(self):
        return {
            "enabled": True,
            "intensity": "MEDIUM",
            "actions_per_hour": 60,
            "allowed_hours_start": 7,
            "allowed_hours_end": 23,
            "search_poison": True,
            "ad_pollution": True,
            "location_spoof": False,
            "fingerprint": True,
            "cookie_saturation": True,
            "app_signal": False,
            "dns_noise": True,
            "layer0_enabled": True,
            "layer1_enabled": False,
            "layer2_enabled": False,
            "layer3_enabled": True,
            "theme": "#d4a853",
            "api_key": "a247c8d858733a9cde76c2974d4e02ef0c4bcde4232da8145ddf76862f827293"
        }
    
    def _save(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self._settings, f, indent=2)
    
    def get(self, key, default=None):
        return self._settings.get(key, default)
    
    def set(self, key, value):
        self._settings[key] = value
        self._save()
    
    def get_all(self):
        return self._settings.copy()
    
    def update(self, data):
        self._settings.update(data)
        self._save()
    
    def has(self, key) -> bool:
        return key in self._settings


def get_settings():
    return SettingsManager()
