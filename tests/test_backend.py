import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, '/home/steimer/fauxx-docker/backend')

from app.settings import SettingsManager
from app.database import get_db


class TestSettingsManager:
    def test_load_settings(self):
        settings = SettingsManager()
        data = settings.get_all()
        assert isinstance(data, dict)

    def test_save_settings(self):
        settings = SettingsManager()
        test_key = "test_value_123"
        settings.set(test_key, test_key)
        assert settings.get(test_key) == test_key


class TestDatabase:
    def test_get_db(self):
        # Should return an async generator
        db_gen = get_db()
        assert hasattr(db_gen, '__anext__') or callable(db_gen)


class TestModules:
    def test_search_module_exists(self):
        from app.modules.search import SearchPoisonModule
        assert SearchPoisonModule is not None

    def test_ads_module_exists(self):
        from app.modules.ads import AdPollutionModule
        assert AdPollutionModule is not None


class TestPersonaSystem:
    def test_persona_pool_loaded(self):
        from app.targeting.layer3 import PERSONA_POOL
        assert len(PERSONA_POOL) >= 32

    def test_get_persona_from_pool(self):
        from app.targeting.layer3 import get_persona_from_pool
        persona = get_persona_from_pool()
        assert persona is not None
        assert 'name' in persona
