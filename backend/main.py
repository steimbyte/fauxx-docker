from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router as api_router, set_engine
from app.api.websocket import router as ws_router
from app.database import engine, Base
from app.targeting.engine import TargetingEngine
from app.targeting.layer0 import UniformEntropyLayer
from app.targeting.layer1 import SelfReportLayer, DemographicDistanceMap
from app.targeting.layer2 import AdversarialScraperLayer
from app.targeting.layer3 import PersonaRotationLayer, PersonaGenerator
from app.modules.search import SearchPoisonModule
from app.modules.ads import AdPollutionModule
from app.modules.cookies import CookieSaturationModule
from app.modules.dns import DnsNoiseModule
from app.modules.fingerprint import FingerprintModule
from app.modules.location import LocationSpoofModule
from app.modules.appsignal import AppSignalModule
from app.scheduler.engine import PoisonEngine, PoisonConfig
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
    
    # Initialize targeting engine
    assets_path = os.path.join(os.path.dirname(__file__), "app", "assets")
    
    targeting = TargetingEngine(
        layer0=UniformEntropyLayer(),
        layer1=SelfReportLayer(DemographicDistanceMap(assets_path)),
        layer2=AdversarialScraperLayer(),
        layer3=PersonaRotationLayer(),
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
    
    # Create poison engine
    poison_config = PoisonConfig(enabled=False, actions_per_hour=60)
    engine_instance = PoisonEngine(targeting, modules)
    engine_instance.update_config(poison_config)
    
    # Set engine in API routes
    set_engine(engine_instance)
    
    print("Fauxx-Docker initialized")
    
    yield
    
    # Shutdown
    if engine_instance and engine_instance.is_running():
        await engine_instance.stop()
    await engine.dispose()


app = FastAPI(
    title="Fauxx-Docker API",
    description="Data Poisoning for your everyday tracking",
    version="0.1.0",
    lifespan=lifespan,
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


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse("static/index.html")
