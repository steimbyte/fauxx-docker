# Fauxx-Docker: Data Poisoning Server

**Fork of:** [digital-grease/fauxx](https://github.com/digital-grease/fauxx)
**Goal:** Docker-based data broker poisoning with web dashboard

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Single Container                          │
├─────────────────────────────────────────────────────────────┤
│                      Fauxx Server                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend  │  SQLite DB  │  Playwright       │   │
│  │     :8000        │   /data/    │  (Browser Pool)  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Single container** runs everything: FastAPI + SQLite + Playwright browser automation.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite (aiosqlite) |
| Browser Automation | Playwright (Chromium) |
| Web Dashboard | React (served by FastAPI) |

---

## Project Structure

```
fauxx-docker/
├── PROJECT.md
├── docker-compose.yml
├── backend/
│   ├── main.py                 # FastAPI entry + web static files
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── action_log.py   # ActionLogEntity
│   │   │   ├── enums.py        # ActionType, CategoryPool, IntensityLevel
│   │   ├── targeting/
│   │   │   ├── engine.py       # TargetingEngine
│   │   │   ├── weight_normalizer.py
│   │   │   ├── layer0.py       # UniformEntropyLayer
│   │   │   ├── layer1.py       # SelfReportLayer + DistanceMap
│   │   │   ├── layer3.py       # PersonaRotationLayer + PersonaGenerator
│   │   ├── modules/
│   │   │   ├── base.py         # Module interface
│   │   │   ├── search.py       # SearchPoisonModule
│   │   │   ├── ads.py          # AdPollutionModule
│   │   │   ├── cookies.py      # CookieSaturationModule
│   │   │   ├── dns.py          # DnsNoiseModule
│   │   │   ├── fingerprint.py   # FingerprintModule
│   │   │   ├── location.py     # LocationSpoofModule (VPN-based)
│   │   │   └── appsignal.py    # AppSignalModule
│   │   ├── scheduler/
│   │   │   ├── engine.py       # PoisonEngine (orchestrator)
│   │   │   ├── dispatcher.py    # ActionDispatcher
│   │   │   └── poisson.py      # PoissonScheduler
│   │   ├── api/
│   │   │   ├── routes.py       # REST endpoints
│   │   └── assets/
│   │       ├── query_banks/    # JSON query corpora
│   │       ├── crawl_urls/     # URL corpus
│   │       ├── city_coords.json
│   │       ├── user_agents.json
│   │       ├── blocklist.json
│   │       └── harmful_queries.json
│   └── static/                 # Web dashboard (built React app)
│       └── index.html
```

---

## TODO List

### Phase 1: Project Setup ✅
- [x] Create docker-compose.yml (single container)
- [x] Set up SQLite database (single file)
- [x] Create FastAPI project structure
- [x] Implement config management
- [x] Create Dockerfile for single container
- [x] Copy assets from fauxx

### Phase 2: Core Data Layer ✅
- [x] Port ActionLogEntity → SQLAlchemy model
- [x] Port CategoryPool enum (30 categories)
- [x] Port ActionType enum
- [x] Port IntensityLevel enum
- [x] Port database.py with async SQLAlchemy + SQLite
- [x] Copy assets from fauxx (query_banks, crawl_urls, city_coords.json, etc.)

### Phase 3: Targeting Engine ✅
- [x] Port WeightNormalizer
- [x] Port UniformEntropyLayer (Layer 0)
- [x] Port SelfReportLayer (Layer 1)
- [x] Port DemographicDistanceMap
- [x] Port AdversarialScraperLayer (Layer 2)
- [x] Port PersonaRotationLayer (Layer 3)
- [x] Port PersonaGenerator
- [x] Port TargetingEngine orchestrator

### Phase 4: Poison Modules ✅
- [x] Port Module interface
- [x] Port SearchPoisonModule (httpx + Markov queries)
- [x] Port MarkovQueryGenerator
- [x] Port DnsNoiseModule
- [x] Port FingerprintModule
- [x] Port AdPollutionModule
- [x] Port CookieSaturationModule
- [x] Port LocationSpoofModule (VPN-based)
- [x] Port AppSignalModule
- [x] Port CrawlListManager + DomainBlocklist
- [x] Port Profile Import (Google/Facebook)

### Phase 5: Scheduling ✅
- [x] Port PoissonScheduler
- [x] Port ActionDispatcher
- [x] Port PoisonEngine (orchestrator)
- [x] Background task runner (asyncio)

### Phase 6: Web Dashboard ✅
- [x] Modern dark UI dashboard (HTML/CSS/JS)
- [x] Dashboard page with stats + charts
- [x] Settings page (intensity, modules, hours)
- [x] Targeting page (layers, persona)
- [x] Action Log viewer with filters
- [x] WebSocket for real-time updates
- [x] Serve static files from FastAPI

### Phase 7: Privacy/Logging ✅
- [x] Port LogScrubber (PII redaction)
- [x] Port EncryptedFileTree (in-memory log storage)
- [x] Port BootGuard (crash loop detection)
- [x] Port CrashDetector + CrashReportWriter

### Phase 8: Testing & Polish
- [ ] Docker build test
- [ ] End-to-end integration test
- [ ] Documentation

---

## Module Mapping (Android → Docker)

| Fauxx (Android) | Fauxx-Docker | Implementation |
|-----------------|--------------|----------------|
| PhantomWebViewPool | httpx + asyncio | Browser automation via HTTP |
| LocationManager.setTestProviderLocation | VPN/Proxy rotation | Rotating residential proxies |
| OkHttpClient | httpx | Async HTTP client |
| WorkManager | asyncio background task | In-container task scheduling |
| Room + SQLCipher | SQLite + SQLAlchemy | Single-file database |
| DataStore | SQLite | Key-value config in DB |
| Foreground Service | Docker container | Always-on process |
| BootReceiver | Docker restart policy | Auto-start |

---

## Key Functions to Implement

### Targeting Engine
```python
# backend/app/targeting/engine.py
class TargetingEngine:
    cached_weights: StateFlow[dict[CategoryPool, float]]
    
    def set_layer1_enabled(enabled: bool)
    def set_layer2_enabled(enabled: bool)
    def set_layer3_enabled(enabled: bool)
    def get_weights() -> Flow[dict[CategoryPool, float]]
```

### Poison Modules
```python
# backend/app/modules/base.py
class Module(ABC):
    @abstractmethod
    async def start()
    @abstractmethod
    async def stop()
    @abstractmethod
    def is_enabled() -> bool
    @abstractmethod
    async def on_action(category: CategoryPool) -> ActionLogEntry
```

### Scheduler
```python
# backend/app/scheduler/poisson.py
class PoissonScheduler:
    def next_delay_ms(
        actions_per_hour: int,
        prev: CategoryPool | None,
        next: CategoryPool | None,
        allowed_start: int,
        allowed_end: int
    ) -> int  # milliseconds
```

---

## Configuration (PoisonProfile)

```python
# runtime config, stored in Redis
{
    "enabled": True,
    "intensity": "MEDIUM",  # LOW(12/hr), MEDIUM(60/hr), HIGH(200/hr)
    "allowed_hours_start": 7,
    "allowed_hours_end": 23,
    "modules": {
        "search_poison": True,
        "ad_pollution": True,
        "location_spoof": False,
        "fingerprint": True,
        "cookie_saturation": True,
        "app_signal": False,
        "dns_noise": True,
    },
    "layers": {
        "layer1": False,  # SelfReport
        "layer2": False,  # AdversarialScraper
        "layer3": True,   # PersonaRotation
    },
    "custom_user_agent": None,
}
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Action counts, active persona |
| GET | `/api/profile` | Get current PoisonProfile |
| PUT | `/api/profile` | Update PoisonProfile |
| GET | `/api/actions` | Paginated action log |
| GET | `/api/actions/stream` | WebSocket for live actions |
| GET | `/api/targeting/weights` | Current category weights |
| POST | `/api/persona/rotate` | Force persona rotation |
| POST | `/api/import/google` | Import Google Takeout |
| POST | `/api/import/facebook` | Import Facebook DYI |
| GET | `/api/logs` | Export action log as JSON |

---

## Asset Files Required

Copy from fauxx/Android assets:
- `assets/query_banks/{locale}/<category>.json` (30 categories × 3 locales)
- `assets/crawl_urls/{locale}.json`
- `assets/city_coords.json` (500+ cities)
- `assets/user_agents.json` (275+ UAs)
- `assets/blocklist.json`
- `assets/harmful_queries/{locale}.json`
- `assets/demographic_distance_rules.json`
- `assets/platform_category_map.json`
- `assets/persona_templates/{locale}.json`

---

## Environment Variables

```env
# Single container - minimal config
DATA_DIR=/data

# Optional
SECRET_KEY=<generate-random-32-bytes>
```

---

## Running Locally

```bash
# Build and start
docker compose up --build -d

# Check health
curl http://localhost:8000/api/health

# View logs
docker compose logs -f

# Stop
docker compose down
```
