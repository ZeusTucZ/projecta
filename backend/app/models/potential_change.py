from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db import Base


class PotentialChange(Base):
    __tablename__ = "potential_changes"

    id = Column(Integer, primary_key=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    affected_trade = Column(
        String(100),
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    status = Column(
        String(50),
        default="pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )