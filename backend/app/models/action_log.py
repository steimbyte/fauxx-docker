from sqlalchemy import Column, BigInteger, String, Boolean, Index
from app.database import Base
from app.models.enums import ActionType, CategoryPool


class ActionLog(Base):
    __tablename__ = "action_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger, default=lambda: int(__import__("time").time() * 1000))
    action_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    detail = Column(String(500), nullable=False)
    success = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_action_log_timestamp_success", "timestamp", "success"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "category": self.category,
            "detail": self.detail,
            "success": self.success,
        }
