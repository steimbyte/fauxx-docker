from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from app.database import Base
from datetime import datetime


class PersonaLog(Base):
    __tablename__ = "persona_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age_range = Column(String(20))
    profession = Column(String(100))
    region = Column(String(50))
    interests = Column(JSON)
    behaviors = Column(JSON)
    activated_at = Column(DateTime, default=datetime.utcnow)
    deactivated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age_range": self.age_range,
            "profession": self.profession,
            "region": self.region,
            "interests": self.interests,
            "behaviors": self.behaviors,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
            "is_active": self.is_active,
        }
