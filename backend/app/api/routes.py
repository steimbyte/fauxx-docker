from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import ActionLog, CategoryPool, IntensityLevel, DailyStats, PersonaLog, SessionData
from app.models.action_log import ActionLog as ActionLogModel
from app.modules.base import ActionLogEntry
from app.models.enums import ActionType
from app.settings import get_settings
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import time

router = APIRouter()

# Global engine instance (set by main.py)
_engine = None


async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from X-API-Key header."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    from app.settings import SettingsManager
    settings = SettingsManager()
    valid_key = settings.get("api_key")
    
    if x_api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


def set_engine(engine):
    global _engine
    _engine = engine


# Request/Response models
class PoisonProfile(BaseModel):
    enabled: bool = True
    intensity: str = "MEDIUM"
    actions_per_hour: Optional[int] = None  # Direct rate override
    allowed_hours_start: int = 7
    allowed_hours_end: int = 23
    search_poison: bool = True
    ad_pollution: bool = True
    location_spoof: bool = False
    fingerprint: bool = True
    cookie_saturation: bool = True
    app_signal: bool = False
    dns_noise: bool = True
    layer0_enabled: bool = True
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
    categories: int = 0  # Number of distinct categories with actions
    modules_active: int = 0  # Number of active modules
    active_persona: Optional[str] = None
    engine_running: bool = False
    data_used_mb: float = 0.0  # Estimated MB used by all actions
    total_actions_all_time: int = 0
    data_used_total_mb: float = 0.0
    engine_uptime_seconds: int = 0


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


@router.get("/auth/key-hint")
async def get_key_hint():
    """Returns first 8 chars of key for hint display."""
    from app.settings import SettingsManager
    settings = SettingsManager()
    key = settings.get("api_key", "")
    return {"hint": key[:8] + "..." if key else None}


async def _save_daily_stats(db: AsyncSession, stats: dict):
    """Save or update daily stats in database."""
    today = date.today()
    
    result = await db.execute(
        select(DailyStats).where(DailyStats.date == today)
    )
    daily = result.scalar_one_or_none()
    
    if daily:
        daily.total_actions = stats["total_actions_today"]
        daily.actions_by_category = stats["actions_by_category"]
        daily.data_used_mb = stats["data_used_mb"]
    else:
        daily = DailyStats(
            date=today,
            total_actions=stats["total_actions_today"],
            actions_by_category=stats["actions_by_category"],
            data_used_mb=stats["data_used_mb"],
        )
        db.add(daily)
    
    await db.commit()


async def _get_cumulative_stats(db: AsyncSession) -> dict:
    """Get cumulative stats from DailyStats table."""
    result = await db.execute(select(func.sum(DailyStats.total_actions)))
    total_all_time = result.scalar() or 0
    
    result = await db.execute(select(func.sum(DailyStats.data_used_mb)))
    data_total = result.scalar() or 0.0
    
    return {"total_all_time": total_all_time, "data_total": data_total}


async def _get_session_value(db: AsyncSession, key: str) -> Optional[str]:
    """Get session value from database."""
    result = await db.execute(
        select(SessionData).where(SessionData.key == key)
    )
    session = result.scalar_one_or_none()
    return session.value if session else None


async def _set_session_value(db: AsyncSession, key: str, value: str):
    """Set session value in database."""
    result = await db.execute(
        select(SessionData).where(SessionData.key == key)
    )
    session = result.scalar_one_or_none()
    
    if session:
        session.value = value
    else:
        session = SessionData(key=key, value=value)
        db.add(session)
    
    await db.commit()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(verify_api_key)):
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
    
    # Count distinct categories with actions
    categories_count = len(by_category)
    
    # Count active modules
    modules_active = 0
    if _engine:
        modules_active = len([m for m in _engine.modules.values() if m.is_enabled()])
    
    engine_running = _engine.is_running() if _engine else False
    
    # Estimate data used (roughly 0.5KB per action)
    data_used_mb = (total_today * 0.0005)
    
    # Get cumulative stats
    cumulative = await _get_cumulative_stats(db)
    total_all_time = cumulative["total_all_time"]
    data_total = cumulative["data_total"]
    
    # Get engine uptime
    uptime_seconds = 0
    if _engine:
        uptime_seconds = _engine.get_uptime_seconds() if hasattr(_engine, 'get_uptime_seconds') else 0
    
    # Build stats dict
    stats = {
        "total_actions_today": total_today,
        "actions_by_category": by_category,
        "categories": categories_count,
        "modules_active": modules_active,
        "active_persona": None,
        "engine_running": engine_running,
        "data_used_mb": round(data_used_mb, 2),
        "total_actions_all_time": total_all_time,
        "data_used_total_mb": round(data_total, 2),
        "engine_uptime_seconds": uptime_seconds,
    }
    
    # Save daily stats
    await _save_daily_stats(db, stats)
    
    return stats


@router.get("/profile", response_model=PoisonProfile)
async def get_profile():
    # Always read from settings.json (single source of truth)
    settings = get_settings()
    
    return PoisonProfile(
        enabled=settings.get("enabled", True),
        intensity=settings.get("intensity", "MEDIUM"),
        actions_per_hour=settings.get("actions_per_hour"),
        allowed_hours_start=settings.get("allowed_hours_start", 7),
        allowed_hours_end=settings.get("allowed_hours_end", 23),
        search_poison=settings.get("search_poison", True),
        ad_pollution=settings.get("ad_pollution", True),
        location_spoof=settings.get("location_spoof", False),
        fingerprint=settings.get("fingerprint", True),
        cookie_saturation=settings.get("cookie_saturation", True),
        app_signal=settings.get("app_signal", False),
        dns_noise=settings.get("dns_noise", True),
        layer0_enabled=settings.get("layer0_enabled", True),
        layer1_enabled=settings.get("layer1_enabled", False),
        layer2_enabled=settings.get("layer2_enabled", False),
        layer3_enabled=settings.get("layer3_enabled", True),
    )


@router.put("/profile")
async def update_profile(profile: PoisonProfile, background_tasks: BackgroundTasks, _=Depends(verify_api_key)):
    # Save to settings.json first
    settings = get_settings()
    
    # Use direct actions_per_hour if provided, otherwise convert from intensity string
    actions_per_hour = profile.actions_per_hour if profile.actions_per_hour else _intensity_to_rate(profile.intensity)
    
    settings.update({
        "enabled": profile.enabled,
        "intensity": profile.intensity,
        "actions_per_hour": actions_per_hour,
        "allowed_hours_start": profile.allowed_hours_start,
        "allowed_hours_end": profile.allowed_hours_end,
        "search_poison": profile.search_poison,
        "ad_pollution": profile.ad_pollution,
        "location_spoof": profile.location_spoof,
        "fingerprint": profile.fingerprint,
        "cookie_saturation": profile.cookie_saturation,
        "app_signal": profile.app_signal,
        "dns_noise": profile.dns_noise,
        "layer0_enabled": profile.layer0_enabled,
        "layer1_enabled": profile.layer1_enabled,
        "layer2_enabled": profile.layer2_enabled,
        "layer3_enabled": profile.layer3_enabled,
    })
    
    # Apply to engine if available
    if _engine:
        from app.scheduler.engine import PoisonConfig
        config = PoisonConfig(
            enabled=profile.enabled,
            actions_per_hour=actions_per_hour,
            allowed_start=profile.allowed_hours_start,
            allowed_end=profile.allowed_hours_end,
        )
        _engine.update_config(config)
        
        # Update module states
        module_map = {
            "search": profile.search_poison,
            "ads": profile.ad_pollution,
            "location": profile.location_spoof,
            "fingerprint": profile.fingerprint,
            "cookies": profile.cookie_saturation,
            "dns": profile.dns_noise,
            "appsignal": profile.app_signal,
        }
        for name, enabled in module_map.items():
            if name in _engine.modules:
                _engine.modules[name].set_enabled(enabled)
        
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
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key)
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
async def start_engine(background_tasks: BackgroundTasks, _=Depends(verify_api_key)):
    if _engine and not _engine.is_running():
        background_tasks.add_task(_engine.start)
        return {"status": "ok", "message": "Engine started"}
    return {"status": "error", "message": "Engine already running or not initialized"}


@router.post("/engine/stop")
async def stop_engine(background_tasks: BackgroundTasks, _=Depends(verify_api_key)):
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


@router.put("/targeting/weights")
async def save_weights(weights: dict, _=Depends(verify_api_key)):
    """Save category weights."""
    # Save to settings.json
    settings = get_settings()
    settings.set("category_weights", weights)
    
    # Apply to engine if available
    if _engine:
        try:
            _engine.engine.set_weights(weights)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"success": True, "weights": weights}


@router.post("/engine/trigger")
async def trigger_action(_=Depends(verify_api_key)):
    """Execute a single action manually."""
    if not _engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        result = await _engine.execute_once()
        if result:
            action_dict = {
                "action_type": result.action_type.value if hasattr(result.action_type, 'value') else str(result.action_type),
                "category": result.category.value if hasattr(result.category, 'value') else str(result.category),
                "detail": result.detail,
                "success": result.success,
            }
            return {"success": True, "action": action_dict}
        return {"success": False, "message": "No action executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/persona/rotate")
async def rotate_persona(db: AsyncSession = Depends(get_db), _=Depends(verify_api_key)):
    if _engine and _engine.engine.layer3:
        from app.targeting.layer3 import SyntheticPersona
        persona = _engine.engine.layer3._persona
        
        # Deactivate current persona in DB
        if persona:
            result = await db.execute(
                select(PersonaLog).where(
                    PersonaLog.name == persona.name,
                    PersonaLog.is_active == True
                )
            )
            old_log = result.scalar_one_or_none()
            if old_log:
                old_log.is_active = False
                old_log.deactivated_at = datetime.utcnow()
        
        # Force new persona rotation
        new_persona = _engine.engine.layer3.rotate_to_next()
        
        # Log new persona to DB
        new_log = PersonaLog(
            name=new_persona.name,
            age_range=new_persona.age_range,
            profession=new_persona.profession,
            region=new_persona.region,
            interests=[i.value for i in new_persona.interests],
            behaviors=new_persona.behaviors,
            activated_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(new_log)
        await db.commit()
        
        return {"status": "ok", "message": "Persona rotated", "persona": {
            "name": new_persona.name,
            "age_range": new_persona.age_range,
            "profession": new_persona.profession,
        }}
    return {"status": "error", "message": "Could not rotate persona"}


@router.get("/actions/stream")
async def actions_stream():
    # WebSocket endpoint at /api/ws
    return {"status": "ok", "websocket": "/api/ws"}


@router.post("/import/google")
async def import_google_profile(
    file: UploadFile = File(...),
    _=Depends(verify_api_key)
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
    _=Depends(verify_api_key)
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
async def get_current_persona(db: AsyncSession = Depends(get_db)):
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
    
    # Fallback: get most recent active persona from DB
    result = await db.execute(
        select(PersonaLog)
        .where(PersonaLog.is_active == True)
        .order_by(PersonaLog.activated_at.desc())
        .limit(1)
    )
    log = result.scalar_one_or_none()
    if log:
        return {
            "id": str(log.id),
            "name": log.name,
            "age_range": log.age_range,
            "profession": log.profession,
            "region": log.region,
            "interests": log.interests,
            "active_until": None,
        }
    
    return {"status": "no_persona"}


@router.get("/persona/profiles")
async def get_persona_profiles():
    """Get saved persona profiles."""
    from app.settings import SettingsManager
    settings = SettingsManager()
    data = settings.get_all()
    return data.get("persona_profiles", [])


@router.post("/persona/profiles")
async def save_persona_profile(profile: dict):
    """Save a persona profile."""
    from app.settings import SettingsManager
    settings = SettingsManager()
    data = settings.get_all()
    
    profiles = data.get("persona_profiles", [])
    
    # Add new profile with ID
    profile["id"] = profile.get("name", "").lower().replace(" ", "-")
    profiles.append(profile)
    
    data["persona_profiles"] = profiles
    settings.update(data)
    
    return {"status": "ok", "profile": profile}


@router.delete("/persona/profiles/{profile_id}")
async def delete_persona_profile(profile_id: str, _=Depends(verify_api_key)):
    """Delete a persona profile."""
    from app.settings import SettingsManager
    settings = SettingsManager()
    data = settings.get_all()
    
    profiles = data.get("persona_profiles", [])
    profiles = [p for p in profiles if p.get("id") != profile_id]
    
    data["persona_profiles"] = profiles
    settings.update(data)
    
    return {"status": "ok"}


@router.post("/persona/profiles/{profile_id}/activate")
async def activate_persona_profile(profile_id: str, _=Depends(verify_api_key)):
    """Activate a persona profile."""
    from app.settings import SettingsManager
    settings = SettingsManager()
    data = settings.get_all()
    
    profiles = data.get("persona_profiles", [])
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    
    if profile:
        # Trigger persona rotation with this profile's interests
        if _engine and _engine.engine.layer3:
            _engine.engine.layer3.rotate_to_next(exclude_last=profile["name"])
        return {"status": "ok", "profile": profile}
    
    return {"detail": "Profile not found"}, 404


@router.get("/persona/history")
async def get_persona_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get persona rotation history."""
    result = await db.execute(
        select(PersonaLog)
        .order_by(PersonaLog.activated_at.desc())
        .limit(limit)
    )
    personas = result.scalars().all()
    return {"history": [p.to_dict() for p in personas]}


@router.get("/stats/history")
async def get_stats_history(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get daily stats history."""
    from datetime import timedelta
    from sqlalchemy import desc
    
    start_date = date.today() - timedelta(days=days)
    
    result = await db.execute(
        select(DailyStats)
        .where(DailyStats.date >= start_date)
        .order_by(desc(DailyStats.date))
    )
    stats = result.scalars().all()
    return {"history": [s.to_dict() for s in stats]}


@router.get("/logs")
async def get_logs():
    """Get recent log entries."""
    from app.modules.logging import get_log_storage
    storage = get_log_storage()
    return {"logs": storage.get_recent(100)}


@router.delete("/logs")
async def clear_logs(_=Depends(verify_api_key)):
    """Clear all logs."""
    from app.modules.logging import get_log_storage
    storage = get_log_storage()
    storage.clear()
    return {"status": "ok", "message": "Logs cleared"}


@router.get("/settings/export")
async def export_settings():
    """Export all settings as JSON."""
    from app.settings import get_settings
    settings = get_settings()
    data = settings.get_all()
    return {
        "version": "1.0",
        "exportedAt": datetime.utcnow().isoformat(),
        "settings": data
    }


@router.get("/schedule")
async def get_schedule():
    """Get scheduled intensity changes."""
    from app.settings import get_settings
    settings = get_settings()
    data = settings.get_all()
    return data.get("schedule", [])


@router.put("/schedule")
async def update_schedule(schedules: list, _=Depends(verify_api_key)):
    """Update scheduled intensity changes."""
    from app.settings import get_settings
    settings = get_settings()
    settings.update({"schedule": schedules})
    return {"status": "ok", "schedule": schedules}
