import time
import json
from pathlib import Path
from datetime import datetime
from app.models.enums import ActionType, CategoryPool


class LogEntry:
    """A single log entry with PII scrubbing."""
    
    def __init__(self, timestamp: int, level: str, message: str, data: dict = None):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.data = data or {}
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "data": self.data,
        }


class LogScrubber:
    """
    Removes PII from logs before export.
    Based on Fauxx Android LogScrubber.
    """
    
    # Patterns to redact
    PII_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
    ]
    
    def __init__(self):
        import re
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.PII_PATTERNS
        ]
    
    def scrub(self, text: str) -> str:
        """Remove PII from text."""
        result = text
        for pattern, replacement in self.compiled_patterns:
            result = pattern.sub(replacement, result)
        return result


class EncryptedFileTree:
    """
    In-memory log storage (simplified from Fauxx encrypted version).
    For production, would use proper encryption.
    """
    
    MAX_ENTRIES = 500
    MAX_AGE_MS = 48 * 60 * 60 * 1000  # 48 hours
    
    def __init__(self):
        self.entries = []
        self.scrubber = LogScrubber()
    
    def add_entry(self, level: str, message: str, data: dict = None):
        """Add a log entry."""
        # Scrub PII
        message = self.scrubber.scrub(message)
        
        entry = LogEntry(
            timestamp=int(time.time() * 1000),
            level=level,
            message=message,
            data=data,
        )
        
        self.entries.append(entry)
        
        # Trim if too large
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries = self.entries[-self.MAX_ENTRIES:]
        
        # Cleanup old entries
        self._cleanup_old()
    
    def _cleanup_old(self):
        """Remove entries older than MAX_AGE_MS."""
        cutoff = int(time.time() * 1000) - self.MAX_AGE_MS
        self.entries = [e for e in self.entries if e.timestamp > cutoff]
    
    def get_recent(self, count: int = 100) -> list[dict]:
        """Get most recent log entries."""
        recent = self.entries[-count:] if self.entries else []
        return [e.to_dict() for e in recent]
    
    def get_all(self) -> str:
        """Get all logs as formatted string."""
        lines = []
        for entry in self.entries:
            ts = datetime.fromtimestamp(entry.timestamp / 1000).isoformat()
            lines.append(f"{ts} [{entry.level.upper()}] {entry.message}")
        return '\n'.join(lines)
    
    def clear(self):
        """Clear all logs."""
        self.entries = []


class BootGuard:
    """
    Detects crash loops and enables safe mode.
    Simplified from Fauxx Android version.
    """
    
    SAFE_MODE_THRESHOLD = 2
    BOOT_SUCCESS_DELAY_MS = 4000
    
    def __init__(self):
        self.failed_boots = 0
        self.safe_mode = False
        self.pending_recovery = False
    
    def record_boot_start(self):
        """Record a boot attempt."""
        pass
    
    def record_boot_success(self):
        """Record successful boot."""
        if self.failed_boots > 0:
            self.failed_boots = 0
    
    def is_in_safe_mode(self) -> bool:
        """Check if in safe mode due to crash loops."""
        return self.safe_mode
    
    def mark_recovery_triggered(self):
        """Mark that recovery was triggered."""
        self.pending_recovery = True
    
    def consume_pending_recovery(self) -> bool:
        """Check and clear pending recovery flag."""
        if self.pending_recovery:
            self.pending_recovery = False
            return True
        return False


class CrashDetector:
    """
    Detects previous crashes.
    """
    
    def __init__(self, log_storage: EncryptedFileTree):
        self.log_storage = log_storage
        self.has_crash = False
        self.crash_info = None
    
    def has_crash_report(self) -> bool:
        """Check if there's an unhandled crash report."""
        return self.has_crash
    
    def read_crash_report(self) -> str | None:
        """Read crash report content."""
        return self.crash_info
    
    def dismiss_crash_report(self):
        """Dismiss the crash report."""
        self.has_crash = False
        self.crash_info = None


class CrashReportWriter:
    """
    Writes crash reports with stack trace and recent logs.
    """
    
    def __init__(self, log_storage: EncryptedFileTree):
        self.log_storage = log_storage
    
    def write_crash_report(self, exception: Exception):
        """Write a crash report."""
        import traceback
        
        stack = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        recent_logs = self.log_storage.get_recent(50)
        
        report = {
            "exception": str(exception),
            "stack": stack,
            "recent_logs": recent_logs,
            "timestamp": int(time.time() * 1000),
        }
        
        # Store in log storage
        self.log_storage.add_entry(
            "ERROR",
            f"CRASH: {exception}",
            report
        )


# Global log storage instance
_log_storage = EncryptedFileTree()


def get_log_storage() -> EncryptedFileTree:
    """Get global log storage."""
    return _log_storage
