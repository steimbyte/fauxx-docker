import asyncio
from dataclasses import dataclass
from app.modules.base import Module, ActionLogEntry
from app.models.enums import CategoryPool, ActionType
from app.scheduler.dispatcher import ActionDispatcher
from app.scheduler.poisson import PoissonScheduler
from app.targeting.engine import TargetingEngine


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
    ):
        self.engine = targeting_engine
        self.modules = modules
        self.dispatcher = ActionDispatcher(targeting_engine)
        self.scheduler = PoissonScheduler()
        self.config = PoisonConfig()
        self._running = False
        self._task = None
    
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
        module = enabled_modules[hash(category) % len(enabled_modules)]
        
        # Execute action
        result = await module.on_action(category)
        
        return result
    
    def is_running(self) -> bool:
        return self._running
    
    def update_config(self, config: PoisonConfig):
        """Update engine configuration."""
        self.config = config
