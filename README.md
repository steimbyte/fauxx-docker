# ⚡ FAUXX

### Privacy Poisoning Engine — Forged for Chaos

> *"Make their algorithms choke on synthetic noise."*

![Dashboard Preview](https://raw.githubusercontent.com/steimbyte/fauxx-docker/master/docs/preview.png)

---

## 🔥 What is this?

**FAUXX** is a privacy poisoning dashboard that pollutes your digital fingerprint with synthetic behavior. It generates fake search queries, cookie trails, DNS noise, ad impressions, and location data — all orchestrated through rotating personas.

The goal: poison tracking systems with enough noise that your real profile becomes statistically insignificant.

> **Original FAUXX Android App** — A brilliant concept by the original developer. This Docker port brings the same power to the browser with a full self-hosted dashboard.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Uvicorn |
| Database | SQLite |
| Frontend | Vanilla JS (no framework, pure performance) |
| Container | Docker + Docker Compose |

---

## ⚙️ Features

### 🎭 Persona System
- **32 pre-built personas** with distinct interests, behaviors, and demographics
- **40-hour auto-rotation** — personas cycle automatically
- **Layer 3 targeting** — persona-weighted category selection

### 🎯 Poison Modules
| Module | Function |
|--------|----------|
| **SearchPoison** | Fake search queries across DuckDuckGo, Bing, Yahoo, Yandex |
| **AdPollution** | Phantom ad impressions and clicks |
| **CookieSaturation** | Pollute tracking cookies with synthetic browsing |
| **DnsNoise** | Generate DNS noise across random domains |
| **FingerprintModule** | Rotate browser fingerprints continuously |
| **LocationSpoof** | Generate location signals from random regions |
| **AppSignal** | Fake app telemetry patterns |

### 🎚️ Intensity Control
| Preset | Actions/Hour |
|--------|--------------|
| LOW | 12 |
| MEDIUM | 60 |
| HIGH | 200 |
| V.HIGH | 1,000 |
| **MAX** | **10,000** |

### 🧠 Targeting Layers
- **Layer 0** — Uniform baseline (all categories equal)
- **Layer 1** — Manual weight adjustment
- **Layer 2** — Schedule-based intensity modulation
- **Layer 3** — Persona-driven interest distribution (65% persona, 35% uniform)

---

## 🚀 Quick Start

### Option 1: Docker Hub (Recommended)
```bash
mkdir fauxx && cd fauxx
curl -O https://raw.githubusercontent.com/steimbyte/fauxx-docker/master/docker-compose-hub.yml
docker compose -f docker-compose-hub.yml up -d
```

### Option 2: Build Locally
```bash
git clone https://github.com/steimbyte/fauxx-docker.git
cd fauxx-docker
docker compose up -d --build
```

### Access Dashboard
```
http://localhost:8000/login
```

### API Key
Default key: `a247c8d858733a9cde76c2974d4e02ef0c4bcde4232da8145ddf76862f827293`

---

## 📊 Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  FAUXX v2.0          [AUTH OK] [WSS CONN] [ENG RUN]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │ 4,231  │ │  89.2%  │ │  32     │ │ 00:23:41│         │
│  │ACTIONS  │ │SUCCESS  │ │PERSONAS │ │ UPTIME  │         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
│                                                         │
│  [═══════════════════════════════] ▓▓▓▓▓░░░░ 60/hr     │
│                                                         │
│  MODULES:  [■ SearchPoison] [■ AdPollution] [■ Cookie]  │
│            [■ DnsNoise]   [■ Fingerprint]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Theme Engine

6 preset themes + custom color picker:

| Theme | Color |
|-------|-------|
| **PHOSPHOR** | `#00ff41` (default) |
| **AMBER** | `#ffb000` |
| **CYAN** | `#00ffff` |
| **MAGENTA** | `#ff00ff` |
| **BLOOD** | `#ff3333` |
| **MIDNIGHT** | `#0066ff` |

---

## 🔐 Security

- API key authentication for all endpoints
- WebSocket secure handshake
- Settings persisted locally (not transmitted)

---

## 📁 Project Structure

```
fauxx-docker/
├── backend/
│   ├── app/
│   │   ├── modules/          # Poison modules
│   │   ├── targeting/        # Layer 0-3 targeting
│   │   ├── scheduler/       # Engine + Poisson distribution
│   │   └── api/             # Routes + WebSocket
│   ├── static/
│   │   └── index.html       # Dashboard UI
│   └── main.py              # FastAPI entry
├── data/                    # Persisted data
├── tests/                   # Test suite
└── docker-compose.yml
```

---

## ⚠️ Disclaimer

This project is for **educational and research purposes**. Privacy poisoning may violate terms of service of tracking platforms. Use responsibly and at your own risk.

---

## 📜 License

MIT License — Do what thou wilt.

---

**Built with malice. Forged in CachyOS.**
