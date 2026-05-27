from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from app.api.routes import router as api_router, set_engine
from app.api.websocket import router as ws_router
from app.database import engine, Base, async_session, async_session as db_session_factory
# Import all models to ensure tables are created
from app.models import ActionLog, PersonaLog, DailyStats, SessionData
from datetime import datetime
from app.targeting.engine import TargetingEngine
from app.targeting.layer0 import UniformEntropyLayer
from app.targeting.layer1 import SelfReportLayer, DemographicDistanceMap
from app.targeting.layer2 import AdversarialScraperLayer
from app.targeting.layer3 import (
    PersonaRotationLayer, 
    PersonaGenerator,
    load_last_persona,
    get_persona_from_pool,
    SyntheticPersona,
)
from app.modules.search import SearchPoisonModule
from app.modules.ads import AdPollutionModule
from app.modules.cookies import CookieSaturationModule
from app.modules.dns import DnsNoiseModule
from app.modules.fingerprint import FingerprintModule
from app.modules.location import LocationSpoofModule
from app.modules.appsignal import AppSignalModule
from app.scheduler.engine import PoisonEngine, PoisonConfig
from app.settings import get_settings
import os


# Global engine instance
engine_instance = None


def get_engine():
    return engine_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_instance
    
    # Startup: create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize targeting engine with random persona from pool
    assets_path = os.path.join(os.path.dirname(__file__), "app", "assets")
    
    # Pick random persona (not same as last on restart)
    last_persona = load_last_persona()
    initial_pool = get_persona_from_pool(exclude_name=last_persona.get("name") if last_persona else None)
    initial_persona = SyntheticPersona.from_pool(initial_pool)
    print(f"Initial persona: {initial_persona.name} ({initial_persona.profession})")
    
    targeting = TargetingEngine(
        layer0=UniformEntropyLayer(),
        layer1=SelfReportLayer(DemographicDistanceMap(assets_path)),
        layer2=AdversarialScraperLayer(),
        layer3=PersonaRotationLayer(persona=initial_persona),
    )
    
    # Initialize modules
    modules = {
        "search": SearchPoisonModule(assets_path),
        "ads": AdPollutionModule(),
        "cookies": CookieSaturationModule(),
        "dns": DnsNoiseModule(assets_path),
        "fingerprint": FingerprintModule(assets_path),
        "location": LocationSpoofModule(assets_path),
        "appsignal": AppSignalModule(),
    }
    
    # Load settings from file
    settings = get_settings()
    
    # Apply module states from settings
    for name, module in modules.items():
        settings_key = _module_to_settings_key(name)
        if settings_key and settings.has(settings_key):
            module.set_enabled(settings.get(settings_key))
    
    # Create poison engine with DB access
    poison_config = PoisonConfig(
        enabled=settings.get("enabled", True),
        actions_per_hour=settings.get("actions_per_hour", 60),
        allowed_start=settings.get("allowed_hours_start", 7),
        allowed_end=settings.get("allowed_hours_end", 23),
    )
    engine_instance = PoisonEngine(targeting, modules, db_session_factory=async_session)
    engine_instance.update_config(poison_config)
    
    # Auto-start the engine
    await engine_instance.start()
    
    # Log initial persona to DB if not already logged
    async with db_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(PersonaLog).where(
                PersonaLog.name == initial_persona.name,
                PersonaLog.is_active == True
            )
        )
        existing = result.scalar_one_or_none()
        if not existing:
            log = PersonaLog(
                name=initial_persona.name,
                age_range=initial_persona.age_range,
                profession=initial_persona.profession,
                region=initial_persona.region,
                interests=[i.value for i in initial_persona.interests],
                behaviors=initial_persona.behaviors,
                activated_at=datetime.utcnow(),
                is_active=True,
            )
            db.add(log)
            await db.commit()
    
    # Set engine in API routes
    set_engine(engine_instance)
    
    print(f"Fauxx-Docker initialized - Engine AUTO-STARTED ({initial_persona.name})")
    
    yield
    
    # Shutdown
    if engine_instance and engine_instance.is_running():
        await engine_instance.stop()
    await engine.dispose()


LOGIN_PAGE = '''<!DOCTYPE html>
<html>
<head>
    <title>Fauxx - Login</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'IBM Plex Sans', sans-serif;
            background: #1a1814;
            color: #e8e4dc;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background: #242019;
            padding: 32px;
            border: 1px solid #3d362c;
            border-radius: 4px;
            width: 320px;
        }
        h1 {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 24px;
            color: #d4a853;
            font-family: 'IBM Plex Mono', monospace;
        }
        input {
            width: 100%;
            padding: 12px;
            background: #2e2820;
            border: 1px solid #3d362c;
            color: #e8e4dc;
            margin-bottom: 16px;
            font-family: 'IBM Plex Mono', monospace;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #d4a853;
            border: none;
            color: #1a1814;
            font-weight: 600;
            cursor: pointer;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        button:hover {
            background: #f0c865;
        }
        .error {
            color: #c45c4a;
            font-size: 12px;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>FAUXX COMMAND CENTER</h1>
        <input type="password" id="apiKey" placeholder="Enter API Key" autocomplete="off">
        <button onclick="login()">AUTHENTICATE</button>
        <div class="error" id="error" style="display:none"></div>
    </div>
    <script>
        function login() {
            const key = document.getElementById('apiKey').value;
            localStorage.setItem('fauxx_api_key', key);
            
            // Verify key works and set cookie
            fetch('/api/engine/status', {
                headers: {'X-API-Key': key}
            }).then(r => {
                if (r.ok) {
                    // Set cookie for server-side auth
                    document.cookie = 'fauxx_key=' + key + '; path=/; SameSite=Strict';
                    window.location.href = '/';
                } else {
                    document.getElementById('error').textContent = 'Invalid API Key';
                    document.getElementById('error').style.display = 'block';
                    localStorage.removeItem('fauxx_api_key');
                }
            }).catch(() => {
                document.getElementById('error').textContent = 'Connection error';
                document.getElementById('error').style.display = 'block';
            });
        }
        
        // Auto-redirect if key exists
        const savedKey = localStorage.getItem('fauxx_api_key');
        if (savedKey) {
            document.getElementById('apiKey').value = savedKey;
            // Try auto-login
            fetch('/api/engine/status', {
                headers: {'X-API-Key': savedKey}
            }).then(r => {
                if (r.ok) {
                    window.location.href = '/';
                }
            }).catch(() => {});
        }
        
        // Enter key submits
        document.getElementById('apiKey').addEventListener('keypress', e => {
            if (e.key === 'Enter') login();
        });
    </script>
</body>
</html>'''

app = FastAPI(
    title="Fauxx-Docker API",
    description="Data Poisoning for your everyday tracking",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow all hosts for reverse proxy compatibility
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/api")


# Serve static files (dashboard)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/login")
async def login_page():
    return HTMLResponse(LOGIN_PAGE)


@app.get("/")
async def root(request: Request):
    key = request.cookies.get('fauxx_key') or request.headers.get('X-API-Key')
    if not key:
        return RedirectResponse('/login')
    
    from app.settings import SettingsManager
    settings = SettingsManager()
    if key != settings.get('api_key'):
        return RedirectResponse('/login')
    
    return FileResponse(
        "static/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/dashboard")
async def dashboard():
    return FileResponse(
        "static/index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/api/version")
async def get_version():
    return {
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


def _module_to_settings_key(module_name: str) -> str:
    """Map module internal name to settings.json key."""
    mapping = {
        "search": "search_poison",
        "ads": "ad_pollution",
        "location": "location_spoof",
        "fingerprint": "fingerprint",
        "cookies": "cookie_saturation",
        "dns": "dns_noise",
        "appsignal": "app_signal",
    }
    return mapping.get(module_name)
