import asyncio
import random
import time
from dataclasses import dataclass
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType
from app.scheduler.dispatcher import ActionDispatcher
from app.scheduler.poisson import PoissonScheduler
from app.targeting.engine import TargetingEngine
from app.models.action_log import ActionLog


async def broadcast_action(action_data: dict):
    """Import broadcast function to avoid circular imports."""
    from app.api.websocket import broadcast_action as _broadcast
    await _broadcast(action_data)


@dataclass
class PoisonConfig:
    """Configuration for poison engine."""
    enabled: bool = False
    actions_per_hour: int = 60  # MEDIUM
    allowed_start: int = 7
    allowed_end: int = 23


class PoisonEngine:
    """
    Main orchestrator for poison operations.
    Coordinates all modules via Poisson scheduling.
    """
    
    def __init__(
        self,
        targeting_engine: TargetingEngine,
        modules: dict[str, Module],
        db_session_factory=None,
    ):
        self.engine = targeting_engine
        self.modules = modules
        self.dispatcher = ActionDispatcher(targeting_engine)
        self.scheduler = PoissonScheduler()
        self.config = PoisonConfig()
        self._running = False
        self._task = None
        self._db_factory = db_session_factory
    
    async def start(self):
        """Start the poison engine."""
        if self._running:
            return
        
        self._running = True
        
        # Start all modules
        for module in self.modules.values():
            if hasattr(module, 'start'):
                await module.start()
        
        # Start main loop
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self):
        """Stop the poison engine."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Stop all modules
        for module in self.modules.values():
            if hasattr(module, 'stop'):
                await module.stop()
    
    async def _run_loop(self):
        """Main action loop with Poisson scheduling."""
        while self._running:
            try:
                await self._execute_action()
                
                # Wait for next Poisson delay
                delay = self.scheduler.next_delay_ms(
                    actions_per_hour=self.config.actions_per_hour,
                    allowed_start=self.config.allowed_start,
                    allowed_end=self.config.allowed_end,
                )
                await asyncio.sleep(delay / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in poison loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def execute_once(self):
        """Execute a single action manually (for manual trigger button)."""
        return await self._execute_action()
    
    async def _execute_action(self):
        """Execute one poison action."""
        # Select category based on weights
        category = self.dispatcher.select_category()
        
        # Find enabled module for this category
        # Round-robin through modules
        enabled_modules = [
            m for m in self.modules.values() 
            if m.is_enabled()
        ]
        
        if not enabled_modules:
            return
        
        # Pick a random enabled module
        module = random.choice(enabled_modules)
        
        # Execute action
        result = await module.on_action(category)
        
        # Save to database and broadcast
        if result:
            await self._save_and_broadcast(result)
        
        return result
    
    async def _save_and_broadcast(self, entry: ActionLogEntry):
        """Save action to DB and broadcast to WebSocket clients."""
        timestamp = int(time.time() * 1000)
        
        # Save to database
        if self._db_factory:
            async with self._db_factory() as session:
                log = ActionLog(
                    timestamp=timestamp,
                    action_type=entry.action_type.value if hasattr(entry.action_type, 'value') else str(entry.action_type),
                    category=entry.category.value if hasattr(entry.category, 'value') else str(entry.category),
                    detail=entry.detail,
                    success=entry.success,
                )
                session.add(log)
                await session.commit()
        
        # Broadcast to WebSocket clients
        await broadcast_action({
            "id": 0,  # Will be updated by frontend
            "timestamp": timestamp,
            "action_type": entry.action_type.value if hasattr(entry.action_type, 'value') else str(entry.action_type),
            "category": entry.category.value if hasattr(entry.category, 'value') else str(entry.category),
            "detail": entry.detail,
            "success": entry.success,
        })
    
    def is_running(self) -> bool:
        return self._running
    
    def update_config(self, config: PoisonConfig):
        """Update engine configuration."""
        self.config = config
