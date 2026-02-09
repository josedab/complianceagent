"""Architecture advisor database models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class ArchitectureReview(Base, UUIDMixin, TimestampMixin):
    """An architecture review run."""

    __tablename__ = "architecture_reviews"

    repository: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Score
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    grade: Mapped[str] = mapped_column(String(5), default="F")
    max_score: Mapped[float] = mapped_column(Float, default=100.0)

    # Counts
    total_patterns_detected: Mapped[int] = mapped_column(Integer, default=0)
    anti_patterns_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended_patterns_count: Mapped[int] = mapped_column(Integer, default=0)
    total_risks: Mapped[int] = mapped_column(Integer, default=0)

    # Detailed results as JSON
    detected_patterns: Mapped[dict] = mapped_column(JSONBType, default=dict)
    risks: Mapped[dict] = mapped_column(JSONBType, default=dict)
    recommendations: Mapped[list[str]] = mapped_column(
        ArrayType(String), default=list
    )
    regulations_analyzed: Mapped[list[str]] = mapped_column(
        ArrayType(String), default=list
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="completed", index=True
    )

    # AI metadata
    ai_enhanced: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"<ArchitectureReview {self.repository} ({self.grade})>"


class ArchitectureRiskRecord(Base, UUIDMixin, TimestampMixin):
    """Individual architecture risk stored for tracking and trending."""

    __tablename__ = "architecture_risk_records"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, nullable=False, index=True
    )
    repository: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Risk details
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_files: Mapped[list[str]] = mapped_column(
        ArrayType(String), default=list
    )
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulations: Mapped[list[str]] = mapped_column(
        ArrayType(String), default=list
    )

    # Resolution tracking
    is_resolved: Mapped[bool] = mapped_column(default=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ArchitectureRiskRecord {self.title} ({self.severity})>"
