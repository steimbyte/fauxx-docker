from abc import ABC, abstractmethod
from app.models.enums import CategoryPool, ActionType
from dataclasses import dataclass


@dataclass
class ActionLogEntry:
    """Result of a poison action."""
    action_type: ActionType
    category: CategoryPool
    detail: str
    success: bool = True
    error: str = None
    
    def to_dict(self):
        return {
            "action_type": self.action_type.value,
            "category": self.category.value,
            "detail": self.detail,
            "success": self.success,
            "error": self.error,
        }


class Module(ABC):
    """Base interface for all poison modules."""
    
    @abstractmethod
    async def start(self):
        """Initialize module resources."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Cleanup module resources."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if module is enabled."""
        pass
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the module."""
        self._enabled = enabled
    
    @abstractmethod
    async def on_action(self, category: CategoryPool) -> ActionLogEntry:
        """Execute one poison action for the given category."""
        pass
