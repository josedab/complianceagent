"""Compliance testing suite database models."""

import uuid

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


class TestSuiteRun(Base, UUIDMixin, TimestampMixin):
    """A compliance test suite generation run."""

    __tablename__ = "test_suite_runs"

    regulation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Results
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    coverage_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Pattern IDs used
    pattern_ids: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Generated test code stored as JSON list
    generated_tests: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Execution metadata
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="completed", index=True
    )

    def __repr__(self) -> str:
        return f"<TestSuiteRun {self.regulation}/{self.framework} ({self.total_tests} tests)>"


class GeneratedTestRecord(Base, UUIDMixin, TimestampMixin):
    """Individual generated test stored for reuse and tracking."""

    __tablename__ = "generated_test_records"

    suite_run_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, nullable=False, index=True
    )
    regulation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    pattern_id: Mapped[str] = mapped_column(String(200), nullable=False)

    # Test details
    test_name: Mapped[str] = mapped_column(String(500), nullable=False)
    test_code: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validation
    is_valid: Mapped[bool | None] = mapped_column(nullable=True)
    validation_errors: Mapped[list[str]] = mapped_column(
        ArrayType(String), default=list
    )

    # AI metadata
    ai_generated: Mapped[bool] = mapped_column(default=False)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<GeneratedTestRecord {self.test_name}>"
