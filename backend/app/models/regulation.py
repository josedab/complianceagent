"""Regulation and regulatory source models."""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin


if TYPE_CHECKING:
    from app.models.requirement import Requirement


class Jurisdiction(str, Enum):
    """Supported jurisdictions."""

    EU = "eu"
    US_FEDERAL = "us_federal"
    US_CALIFORNIA = "us_california"
    US_NEW_YORK = "us_new_york"
    UK = "uk"
    SINGAPORE = "sg"
    SOUTH_KOREA = "kr"
    CHINA = "cn"
    INDIA = "in"
    JAPAN = "jp"
    BRAZIL = "br"
    AUSTRALIA = "au"
    CANADA = "ca"
    GLOBAL = "global"


class RegulatoryFramework(str, Enum):
    """Regulatory frameworks."""

    GDPR = "gdpr"
    CCPA = "ccpa"
    CPRA = "cpra"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOX = "sox"
    EU_AI_ACT = "eu_ai_act"
    DORA = "dora"
    NIS2 = "nis2"
    SEC_CYBER = "sec_cyber"
    UK_GDPR = "uk_gdpr"
    PIPL = "pipl"
    PDPA = "pdpa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    # Asia-Pacific frameworks
    DPDP = "dpdp"  # India Digital Personal Data Protection
    APPI = "appi"  # Japan Act on Protection of Personal Information
    PIPA = "pipa"  # South Korea Personal Information Protection Act
    # ESG & Sustainability frameworks
    CSRD = "csrd"  # EU Corporate Sustainability Reporting Directive
    SEC_CLIMATE = "sec_climate"  # SEC Climate Disclosure Rules
    TCFD = "tcfd"  # Task Force on Climate-related Financial Disclosures
    # AI Safety frameworks
    NIST_AI_RMF = "nist_ai_rmf"  # NIST AI Risk Management Framework
    ISO42001 = "iso42001"  # ISO AI Management System
    # Other frameworks
    LGPD = "lgpd"  # Brazil General Data Protection Law
    FERPA = "ferpa"  # US Family Educational Rights and Privacy Act
    WCAG = "wcag"  # Web Content Accessibility Guidelines


class RegulationStatus(str, Enum):
    """Regulation status."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    ADOPTED = "adopted"
    EFFECTIVE = "effective"
    AMENDED = "amended"
    REPEALED = "repealed"


class ChangeType(str, Enum):
    """Type of regulatory change."""

    NEW = "new"
    AMENDMENT = "amendment"
    GUIDANCE = "guidance"
    INTERPRETATION = "interpretation"
    ENFORCEMENT = "enforcement"
    REPEAL = "repeal"


class RegulatorySource(Base, UUIDMixin, TimestampMixin):
    """Regulatory source being monitored."""

    __tablename__ = "regulatory_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    jurisdiction: Mapped[Jurisdiction] = mapped_column(String(50), nullable=False)
    framework: Mapped[RegulatoryFramework | None] = mapped_column(String(50), nullable=True)

    # Monitoring configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    check_interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_change_detected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # State for change detection
    last_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_etag: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Reliability tracking
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    successful_checks: Mapped[int] = mapped_column(Integer, default=0)

    # Parser configuration
    parser_type: Mapped[str] = mapped_column(String(50), default="html")
    parser_config: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    regulations: Mapped[list["Regulation"]] = relationship(
        "Regulation", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RegulatorySource {self.name}>"


class Regulation(Base, UUIDMixin, TimestampMixin):
    """A regulation or regulatory document."""

    __tablename__ = "regulations"

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("regulatory_sources.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Identification
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    official_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jurisdiction: Mapped[Jurisdiction] = mapped_column(String(50), nullable=False, index=True)
    framework: Mapped[RegulatoryFramework] = mapped_column(String(50), nullable=False, index=True)

    # Status and dates
    status: Mapped[RegulationStatus] = mapped_column(String(50), default=RegulationStatus.EFFECTIVE)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    enforcement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Content
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text_s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Change tracking
    change_type: Mapped[ChangeType | None] = mapped_column(String(50), nullable=True)
    parent_regulation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType,
        ForeignKey("regulations.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    # AI processing status
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parsing_confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Metadata
    tags: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    extra_metadata: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    source: Mapped["RegulatorySource | None"] = relationship(
        "RegulatorySource", back_populates="regulations"
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        "Requirement", back_populates="regulation", cascade="all, delete-orphan"
    )
    amendments: Mapped[list["Regulation"]] = relationship(
        "Regulation",
        backref="parent_regulation",
        remote_side="Regulation.id",
        foreign_keys="Regulation.parent_regulation_id",
    )

    def __repr__(self) -> str:
        return f"<Regulation {self.short_name or self.name}>"
