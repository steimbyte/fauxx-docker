from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import ActionLog, CategoryPool, IntensityLevel
from app.models.action_log import ActionLog as ActionLogModel
from app.modules.base import ActionLogEntry
from app.models.enums import ActionType
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import time

router = APIRouter()

# Global engine instance (set by main.py)
_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


# Request/Response models
class PoisonProfile(BaseModel):
    enabled: bool = True
    intensity: str = "MEDIUM"
    allowed_hours_start: int = 7
    allowed_hours_end: int = 23
    search_poison: bool = True
    ad_pollution: bool = True
    location_spoof: bool = False
    fingerprint: bool = True
    cookie_saturation: bool = True
    app_signal: bool = False
    dns_noise: bool = True
    layer1_enabled: bool = False
    layer2_enabled: bool = False
    layer3_enabled: bool = True


class ActionLogResponse(BaseModel):
    id: int
    timestamp: int
    action_type: str
    category: str
    detail: str
    success: bool


class StatsResponse(BaseModel):
    total_actions_today: int
    actions_by_category: dict
    active_persona: Optional[str] = None
    engine_running: bool = False


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class EngineStatusResponse(BaseModel):
    running: bool
    actions_per_hour: int
    enabled_modules: list[str]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    start_of_day = int(datetime(now.year, now.month, now.day).timestamp() * 1000)
    
    # Count today's actions
    result = await db.execute(
        select(func.count(ActionLogModel.id)).where(
            ActionLogModel.timestamp >= start_of_day,
            ActionLogModel.success == True
        )
    )
    total_today = result.scalar() or 0
    
    # Actions by category
    result = await db.execute(
        select(ActionLogModel.category, func.count(ActionLogModel.id))
        .where(ActionLogModel.timestamp >= start_of_day)
        .group_by(ActionLogModel.category)
    )
    by_category = {row[0]: row[1] for row in result.fetchall()}
    
    engine_running = _engine.is_running() if _engine else False
    
    return {
        "total_actions_today": total_today,
        "actions_by_category": by_category,
        "active_persona": None,
        "engine_running": engine_running,
    }


@router.get("/profile", response_model=PoisonProfile)
async def get_profile():
    if _engine:
        config = _engine.config
        return PoisonProfile(
            enabled=config.enabled,
            intensity=_intensity_from_rate(config.actions_per_hour),
            allowed_hours_start=config.allowed_start,
            allowed_hours_end=config.allowed_end,
        )
    return PoisonProfile()


@router.put("/profile")
async def update_profile(profile: PoisonProfile, background_tasks: BackgroundTasks):
    if _engine:
        from app.scheduler.engine import PoisonConfig
        config = PoisonConfig(
            enabled=profile.enabled,
            actions_per_hour=_intensity_to_rate(profile.intensity),
            allowed_start=profile.allowed_hours_start,
            allowed_end=profile.allowed_hours_end,
        )
        _engine.update_config(config)
        
        if profile.enabled and not _engine.is_running():
            background_tasks.add_task(_engine.start)
        elif not profile.enabled and _engine.is_running():
            background_tasks.add_task(_engine.stop)
    
    return {"status": "ok", "profile": profile}


def _intensity_from_rate(rate: int) -> str:
    if rate <= 12:
        return "LOW"
    elif rate <= 60:
        return "MEDIUM"
    return "HIGH"


def _intensity_to_rate(intensity: str) -> int:
    return {
        "LOW": 12,
        "MEDIUM": 60,
        "HIGH": 200,
    }.get(intensity, 60)


@router.get("/actions", response_model=list[ActionLogResponse])
async def get_actions(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ActionLogModel)
        .order_by(ActionLogModel.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    actions = result.scalars().all()
    return [ActionLogResponse(**a.to_dict()) for a in actions]


@router.post("/engine/start")
async def start_engine(background_tasks: BackgroundTasks):
    if _engine and not _engine.is_running():
        background_tasks.add_task(_engine.start)
        return {"status": "ok", "message": "Engine started"}
    return {"status": "error", "message": "Engine already running or not initialized"}


@router.post("/engine/stop")
async def stop_engine(background_tasks: BackgroundTasks):
    if _engine and _engine.is_running():
        background_tasks.add_task(_engine.stop)
        return {"status": "ok", "message": "Engine stopped"}
    return {"status": "error", "message": "Engine not running"}


@router.get("/engine/status", response_model=EngineStatusResponse)
async def get_engine_status():
    if not _engine:
        return EngineStatusResponse(running=False, actions_per_hour=0, enabled_modules=[])
    
    enabled = [
        name for name, m in _engine.modules.items()
        if m.is_enabled()
    ]
    
    return EngineStatusResponse(
        running=_engine.is_running(),
        actions_per_hour=_engine.config.actions_per_hour,
        enabled_modules=enabled,
    )


@router.get("/targeting/weights")
async def get_weights():
    if _engine:
        weights = _engine.engine.get_weights()
        return {"weights": {k.value: v for k, v in weights.items()}}
    return {"weights": {c.value: 1.0 / len(CategoryPool) for c in CategoryPool}}


@router.post("/persona/rotate")
async def rotate_persona():
    if _engine and _engine.engine.layer3:
        from app.targeting.layer3 import SyntheticPersona
        persona = _engine.engine.layer3._persona
        # Force new persona by clearing current
        if persona:
            _engine.engine.layer3._persona = None
        return {"status": "ok", "message": "Persona rotated"}
    return {"status": "error", "message": "Could not rotate persona"}


@router.get("/actions/stream")
async def actions_stream():
    # WebSocket endpoint at /api/ws
    return {"status": "ok", "websocket": "/api/ws"}


@router.post("/import/google")
async def import_google_profile(
    file: UploadFile = File(...),
):
    """Import Google Takeout profile."""
    try:
        content = await file.read()
        
        from app.modules.importers import GoogleTakeoutImporter, CategoryMapper
        
        assets_path = None  # Will use fallback heuristics
        mapper = CategoryMapper(assets_path)
        importer = GoogleTakeoutImporter(mapper)
        
        result = await importer.import_profile(content, file.filename)
        
        if result.success:
            return {
                "status": "ok",
                "message": result.message,
                "categories_found": result.categories_found,
            }
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": result.message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/import/facebook")
async def import_facebook_profile(
    file: UploadFile = File(...),
):
    """Import Facebook DYI profile."""
    try:
        content = await file.read()
        
        from app.modules.importers import FacebookDyiImporter, CategoryMapper
        
        assets_path = None
        mapper = CategoryMapper(assets_path)
        importer = FacebookDyiImporter(mapper)
        
        result = await importer.import_profile(content, file.filename)
        
        if result.success:
            return {
                "status": "ok",
                "message": result.message,
                "categories_found": result.categories_found,
            }
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": result.message}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.get("/persona/current")
async def get_current_persona():
    """Get current active persona."""
    if _engine and _engine.engine.layer3:
        persona = _engine.engine.layer3._persona
        if persona:
            return {
                "id": persona.id,
                "name": persona.name,
                "age_range": persona.age_range,
                "profession": persona.profession,
                "region": persona.region,
                "interests": [i.value for i in persona.interests],
                "active_until": persona.active_until,
            }
    return {"status": "no_persona"}


@router.get("/logs")
async def get_logs():
    """Get recent log entries."""
    from app.modules.logging import get_log_storage
    storage = get_log_storage()
    return {"logs": storage.get_recent(100)}


@router.delete("/logs")
async def clear_logs():
    """Clear all logs."""
    from app.modules.logging import get_log_storage
    storage = get_log_storage()
    storage.clear()
    return {"status": "ok", "message": "Logs cleared"}
