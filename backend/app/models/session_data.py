from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base
from datetime import datetime


class SessionData(Base):
    __tablename__ = "session_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(500))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
