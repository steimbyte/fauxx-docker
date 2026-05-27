# Fauxx - Privacy Poisoning Dashboard

**Version:** 1.1.0  
**Status:** Active Development  
**Stack:** FastAPI + SQLite + Vanilla JS/CSS  
**Last Updated:** 2026-05-27

**Docker Hub:** `steimerbyte/fauxx:latest`  
**GitHub:** https://github.com/steimbyte/fauxx-docker

---

## Table of Contents

1. [Architecture](#architecture)
2. [Features](#features)
3. [API Endpoints](#api-endpoints)
4. [Database Tables](#database-tables)
5. [Design System](#design-system)
6. [Specs & Requirements](#specs--requirements)
7. [Do's and Don'ts](#dos-and-donts)
8. [Known Bugs & Fixes](#known-bugs--fixes)
9. [Potential Issues](#potential-issues)
10. [Todo List](#todo-list)
11. [Development](#development)

---

## Architecture

```
fauxx-docker/
├── backend/                    # Python FastAPI backend
│   ├── main.py               # Entry point, lifespan, startup
│   ├── settings.py           # SettingsManager (singleton)
│   ├── config.py             # Configuration
│   ├── database.py           # SQLite connection
│   ├── static/
│   │   └── index.html       # Single-page dashboard (SPA)
│   └── app/
│       ├── api/
│       │   ├── routes.py    # REST endpoints
│       │   └── websocket.py  # WebSocket live updates
│       ├── models/
│       │   ├── action_log.py
│       │   ├── persona_log.py
│       │   ├── stats_history.py
│       │   ├── session_data.py
│       │   └── enums.py
│       ├── modules/
│       │   ├── base.py
│       │   ├── search.py
│       │   ├── ads.py
│       │   ├── cookies.py
│       │   ├── dns.py
│       │   ├── fingerprint.py
│       │   ├── location.py
│       │   ├── appsignal.py
│       │   ├── crawllist.py
│       │   ├── importers.py
│       │   └── logging.py
│       ├── scheduler/
│       │   ├── engine.py
│       │   ├── dispatcher.py
│       │   └── poisson.py
│       ├── targeting/
│       │   ├── engine.py
│       │   ├── layer0.py
│       │   ├── layer1.py
│       │   ├── layer2.py
│       │   ├── layer3.py
│       │   └── weight_normalizer.py
│       └── assets/
│           ├── query_banks/
│           ├── crawl_urls/
│           ├── persona_templates/
│           └── harmful_queries/
├── data/
│   ├── settings.json
│   └── last_persona.json
├── tests/
│   └── test_dashboard.py
├── docker-compose.yml
└── PROJECT.md
```

---

## Features

### Poison Modules (7)
| Module | Backend Key | Purpose |
|--------|-------------|---------|
| SearchPoison | `search_poison` | Pollute search results |
| AdPollution | `ad_pollution` | Fake ad impressions |
| CookieSaturation | `cookie_saturation` | Flood sites with cookies |
| DnsNoise | `dns_noise` | DNS noise traffic |
| FingerprintModule | `fingerprint` | Diverse browser fingerprints |
| LocationSpoof | `location_spoof` | Fake geo locations |
| AppSignal | `app_signal` | App signal noise |

### Targeting Layers (4)
| Layer | Name | Function |
|-------|------|----------|
| L0 | Category | Weighted random category selection |
| L1 | Platform | Google, Facebook, etc. |
| L2 | Query | Search query generation |
| L3 | Persona | Persona assignment |

### Personas
- 32 pre-defined personas
- Auto-rotate every 40 hours
- Persisted to `last_persona.json`

### Intensity Control
- Slider: 1-200 actions/hour (maps to 0-100)
- Custom: 1-1000 actions/hour
- Saved to `settings.json` as `actions_per_hour`
- Engine reads and respects value immediately

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile` | Get current profile |
| PUT | `/api/profile` | Update profile (saves to settings.json) |
| GET | `/api/stats` | Get engine stats |
| POST | `/api/engine/start` | Start engine |
| POST | `/api/engine/stop` | Stop engine |
| GET | `/api/engine/status` | Get engine status |
| GET | `/api/engine/trigger` | Manual trigger (no rate limit) |
| GET | `/api/actions` | Get action logs |
| GET | `/api/targeting/weights` | Get category weights |
| PUT | `/api/targeting/weights` | Update weights (saves to settings.json) |
| GET | `/api/persona/current` | Get current persona |
| POST | `/api/persona/rotate` | Rotate persona |
| GET | `/api/persona/history` | Get persona history |
| GET | `/api/stats/history` | Get daily stats |
| POST | `/api/import/google` | Import Chrome data |
| POST | `/api/import/facebook` | Import Facebook data |
| WS | `/api/ws` | WebSocket for live updates |

---

## Database Tables

### action_logs
```sql
id, timestamp, module, category, platform, action_type, 
status, endpoint, url, request_data, response_data, 
error, persona_name, data_used_bytes
```

### persona_logs
```sql
id, name, age_range, profession, region, interests, 
behaviors, activated_at, deactivated_at, is_active
```

### daily_stats
```sql
id, date, total_actions, actions_by_category, 
data_used_mb, active_hours
```

### session_data
```sql
id, key, value, updated_at
```

---

## Design System

### Colors (Retro-Futurism / CIA Terminal)
```css
/* CRT Phosphor Green Terminal */
--bg-deep: #0a0a0a;         /* deep black */
--bg-panel: #0f0f0f;         /* panel black */
--bg-surface: #141414;       /* surface black */
--bg-module: #1a1a1a;        /* module black */

/* Green phosphor spectrum */
--text-primary: #00ff41;     /* phosphor green */
--text-secondary: #00cc33;   /* dim green */
--text-data: #33ff66;        /* bright green */
--text-muted: #006622;       /* muted green */

/* Amber accent */
--accent: #ffb000;           /* amber */
--accent-dim: #cc8800;       /* dim amber */
--accent-bright: #ffd633;     /* bright amber */

/* Status */
--status-ok: #00ff41;        /* green */
--status-warn: #ffb000;      /* amber */
--status-err: #ff3333;       /* red */
--status-off: #333333;       /* off */

/* Effects */
--glow: 0 0 10px rgba(0, 255, 65, 0.3);
--border: 1px solid #003311;
```

### Typography
- **IBM Plex Sans** - UI text
- **IBM Plex Mono** - Data, labels, numbers

### Border Radius
- `0` for functional elements (inputs, buttons, toggles)
- `4px` for content containers (cards, panels)
- `50%` for dots/indicators only

---

## Specs & Requirements

### Backend
- [x] FastAPI with uvicorn
- [x] SQLite database (not PostgreSQL)
- [x] WebSocket for live updates
- [x] Settings persistence to settings.json
- [x] Engine auto-start on container boot
- [x] 7 poison modules implemented
- [x] 4 targeting layers
- [x] 32 personas with auto-rotation
- [x] API Key Authentication (OpenSSL RAND 32)

### Frontend
- [x] Single-page dashboard (SPA)
- [x] **Retro-Futurism / CIA / NASA Terminal aesthetic**
- [x] CRT Phosphor Green color scheme
- [x] Scanlines overlay effect
- [x] ALL monospace typography (IBM Plex Mono)
- [x] Dense information grids
- [x] Module Status Matrix
- [x] ASCII status indicators
- [x] Theme engine with color presets
- [x] Custom intensity slider (1-1000)
- [x] Action log with filters
- [x] Expand/Collapse all for logs
- [x] Module toggles
- [x] Layer toggles
- [x] Category weight sliders
- [x] Persona display and rotation
- [x] Command Palette (Ctrl+K)
- [x] Dark/Light Theme Toggle
- [x] Login Page with API Key
- [x] PWA Support (manifest + service worker)

### Data Persistence
- [x] settings.json for all settings
- [x] last_persona.json for persona
- [x] SQLite for action logs
- [x] SQLite for persona history
- [x] SQLite for stats history

---

## Do's and Don'ts

### DO
- Use IBM Plex fonts (NOT Space Grotesk, Syne, Unbounded)
- Use warm brown/amber colors (NOT teal/cyan)
- Keep border-radius 0 for functional elements
- Use 4px radius only on outer containers
- Save settings immediately on change
- Read settings from settings.json on engine tick
- Use monospace for data/numbers display
- Use ALL CAPS for labels

### DON'T
- ❌ Space Grotesk, Playfair Display, Syne, Unbounded
- ❌ Teal/Cyan accent (#00e5b8, #00ffff)
- ❌ Fade-up scroll animations
- ❌ Grain/noise overlay on entire page
- ❌ Numbered cards (01, 02, 03)
- ❌ Letter-spacing on labels
- ❌ LED blinking animations
- ❌ Radar sweep animations
- ❌ Centered hero + two buttons layout
- ❌ Logo-left/links-right nav pattern
- ❌ Particle/canvas backgrounds
- ❌ Purple gradients
- ❌ Fade-in stagger animations
- ❌ Numbered section headers
- ❌ Plastic/AI-gradient buttons

---

## Known Bugs & Fixes

| Date | Bug | Fix |
|------|-----|-----|
| 2026-05-26 | Module `set_enabled()` missing | Added method to base.py |
| 2026-05-26 | Module name mismatch | Mapped frontend → backend keys |
| 2026-05-26 | Stats field `total_actions_today` | Fixed in routes.py |
| 2026-05-26 | Stats field `engine_running` | Added to response |
| 2026-05-26 | `facebook` icon not in Lucide | Replaced with `globe` |
| 2026-05-26 | Engine not auto-starting | Added `enabled=True` + `await engine.start()` |
| 2026-05-26 | DB schema BIGINT for autoincrement | Changed to INTEGER |
| 2026-05-26 | Action log not updating | Fixed fetch + WebSocket |
| 2026-05-26 | Anime.js hitbox offset | Used wrapper div approach |
| 2026-05-26 | Intensity slider thumb misalignment | Fixed margin-top + track height |
| 2026-05-26 | Too many border-radius | Reset to 0, kept only on containers |
| 2026-05-26 | WebSocket disconnects without reconnect | Added exponential backoff reconnection logic |
| 2026-05-26 | No loading states | Added skeleton screens for all pages |
| 2026-05-26 | Browser caches old CSS/JS | Added no-cache headers + /api/version endpoint |
| 2026-05-26 | No error boundaries | Added global error handler + safeFetch wrapper |
| 2026-05-26 | Fake Health/Geo panels | Replaced with Engine Stats using real API data |
| 2026-05-26 | No keyboard shortcuts | Added 8 shortcuts (E/T/1-4/R/?) |
| 2026-05-26 | No unit tests | Created test_backend.py with 7 passing tests |
| 2026-05-26 | No command palette | Added Ctrl+K command palette |
| 2026-05-26 | No theme toggle | Added dark/light theme switch |
| 2026-05-26 | No scheduled intensity | Added schedule API + UI |
| 2026-05-26 | No persona profiles | Added save/load persona profiles |
| 2026-05-26 | Animation anti-patterns | Removed transitions, glow, shimmer animations |
| 2026-05-27 | Complete UI redesign | Retro-Futurism / CIA Terminal aesthetic with CRT phosphor green |
| 2026-05-27 | API Key Auth | OpenSSL RAND 32 key + login page + header verification |
| 2026-05-27 | High intensity support | 10,000/hr with 100ms min delay |
| 2026-05-27 | Action Detail Modal | Click action log for full details |
| 2026-05-27 | Weight Normalizer Bug | Fixed sum to 1.0 (was ~2.0) |
| 2026-05-27 | get_profile API | Now returns actions_per_hour |
| 2026-05-27 | TrustedHostMiddleware | Added for reverse proxy support |
| 2026-05-27 | Theme Accent Colors | All text elements use var(--text-primary) |
| 2026-05-27 | Docker Hub Release | Published steimerbyte/fauxx:latest |

---

## Potential Issues

### Backend
- [ ] Persona auto-rotation timer needs DB check (currently uses file time)
- [ ] No rate limiting on API endpoints (except intentional manual trigger)
- [ ] No authentication/authorization
- [ ] SQLite not suitable for concurrent writes (low risk for single-user)

### Frontend
- [x] WebSocket reconnection implemented
- [x] Loading states / skeletons added
- [x] Browser cache busting (no-cache headers)

### Testing
- [x] Backend unit tests (7 passing) ✅
- [x] Integration tests (9 passing, 1 skipped) ✅
- [x] UI polish tests (20 tests) ✅

---

## Todo List

### High Priority
- [x] Fix WebSocket reconnection on disconnect ✅
- [x] Add loading states / skeletons ✅
- [x] Implement browser cache busting ✅
- [x] Test persona auto-rotation with DB ✅

### Medium Priority
- [x] Add authentication (API Key) ✅
- [x] Backend unit tests ✅
- [x] Integration tests ✅
- [x] Error boundaries in frontend ✅

### Low Priority
- [x] Remove irrelevant UI (Health/Geo/Radar) ✅
- [x] Export/import settings profile ✅
- [x] Multiple persona profiles ✅
- [x] Scheduled intensity changes ✅
- [ ] Custom module ordering

### Nice to Have
- [x] Keyboard shortcuts ✅
- [x] Command palette (Ctrl+K) ✅
- [x] Dark/light theme toggle ✅
- [x] Scheduled intensity changes ✅
- [x] Multiple persona profiles ✅
- [ ] Notifications (browser push)
- [ ] Mobile PWA support

---

## Development

### Start Container

### Docker Hub Deployment
```bash
mkdir fauxx && cd fauxx
curl -O https://raw.githubusercontent.com/steimbyte/fauxx-docker/master/docker-compose-hub.yml
docker compose up -d
```

```bash
cd fauxx-docker
docker compose up -d --build
```

### View Logs
```bash
docker logs -f fauxx
```

### Shell Access
```bash
docker exec -it fauxx /bin/bash
```

### Test API
```bash
docker exec fauxx curl http://localhost:8000/api/stats
docker exec fauxx curl http://localhost:8000/api/engine/status
```

### Check Settings
```bash
docker exec fauxx cat /data/settings.json
```

### Check Database
```bash
docker exec fauxx sqlite3 /data/fauxx.db ".tables"
docker exec fauxx sqlite3 /data/fauxx.db "SELECT COUNT(*) FROM action_logs;"
```

### Rebuild Clean
```bash
docker compose down
rm -rf data/*
docker compose up -d --build
```

### Run Playwright Tests
```bash
cd fauxx-docker
pip install playwright
playwright install chromium
pytest tests/test_dashboard.py
```

---

## Contact

For issues or questions, check:
- Session logs in `.fusion/memory/`
- Task history in `.fusion/tasks/`

---

**License:** Internal use only  
**Author:** steimer  
**Created:** 2026-05
