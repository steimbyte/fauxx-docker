from sqlalchemy import Column, Integer, String, JSON, Date, Float
from app.database import Base


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    total_actions = Column(Integer, default=0)
    actions_by_category = Column(JSON)
    data_used_mb = Column(Float, default=0.0)
    active_hours = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "total_actions": self.total_actions,
            "actions_by_category": self.actions_by_category,
            "data_used_mb": self.data_used_mb,
            "active_hours": self.active_hours,
        }
