import pytest
import requests
import time

BASE_URL = "http://localhost:8000"

class TestEngineIntegration:
    def test_engine_start_stop(self):
        # Stop engine
        r = requests.post(f"{BASE_URL}/api/engine/stop")
        assert r.status_code == 200
        
        # Check status
        r = requests.get(f"{BASE_URL}/api/engine/status")
        data = r.json()
        assert data["running"] == False
        
        # Start engine
        r = requests.post(f"{BASE_URL}/api/engine/start")
        assert r.status_code == 200
        
        # Verify running
        r = requests.get(f"{BASE_URL}/api/engine/status")
        data = r.json()
        assert data["running"] == True

    def test_manual_trigger(self):
        r = requests.post(f"{BASE_URL}/api/engine/trigger")
        assert r.status_code == 200
        data = r.json()
        assert "action" in data or "status" in data

class TestProfileIntegration:
    def test_get_profile(self):
        r = requests.get(f"{BASE_URL}/api/profile")
        assert r.status_code == 200
        data = r.json()
        assert "enabled" in data
        assert "intensity" in data

    def test_update_profile(self):
        # Save original
        orig = requests.get(f"{BASE_URL}/api/profile").json()
        
        # Update
        r = requests.put(f"{BASE_URL}/api/profile", json={"intensity": "CUSTOM"})
        assert r.status_code == 200
        
        # Verify
        data = requests.get(f"{BASE_URL}/api/profile").json()
        assert data["intensity"] == "CUSTOM"
        
        # Restore
        requests.put(f"{BASE_URL}/api/profile", json=orig)

class TestPersonaIntegration:
    def test_get_current_persona(self):
        r = requests.get(f"{BASE_URL}/api/persona/current")
        assert r.status_code == 200
        data = r.json()
        assert "name" in data
        
    def test_rotate_persona(self):
        old = requests.get(f"{BASE_URL}/api/persona/current").json()
        
        r = requests.post(f"{BASE_URL}/api/persona/rotate")
        assert r.status_code == 200
        
        new = requests.get(f"{BASE_URL}/api/persona/current").json()
        # May or may not change depending on pool

class TestStatsIntegration:
    def test_get_stats(self):
        r = requests.get(f"{BASE_URL}/api/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_actions_today" in data

    def test_get_actions(self):
        r = requests.get(f"{BASE_URL}/api/actions?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0

class TestTargetingIntegration:
    def test_get_weights(self):
        r = requests.get(f"{BASE_URL}/api/targeting/weights")
        assert r.status_code == 200
        data = r.json()
        assert "weights" in data

class TestWebSocket:
    @pytest.mark.skip(reason="websocket-client not installed")
    def test_websocket_connect(self):
        import websocket
        ws = websocket.create_connection(f"ws://localhost:8000/api/ws")
        assert ws.connected
        ws.close()
