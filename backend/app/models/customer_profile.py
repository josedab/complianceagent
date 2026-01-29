"""Customer profile model for relevance filtering."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import ArrayType, Base, JSONBType, UUIDType
from app.models.base import TimestampMixin, UUIDMixin
from app.models.regulation import Jurisdiction, RegulatoryFramework


if TYPE_CHECKING:
    from app.models.codebase import Repository
    from app.models.organization import Organization


class Industry(str):
    """Industry verticals."""

    FINANCIAL_SERVICES = "financial_services"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    RETAIL = "retail"
    INSURANCE = "insurance"
    GOVERNMENT = "government"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    OTHER = "other"


class CustomerProfile(Base, UUIDMixin, TimestampMixin):
    """Customer profile defining what regulations are relevant."""

    __tablename__ = "customer_profiles"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Profile identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Industry and business context
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_publicly_traded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Geographic scope
    headquarters_jurisdiction: Mapped[Jurisdiction | None] = mapped_column(
        String(50), nullable=True
    )
    operating_jurisdictions: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    customer_jurisdictions: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Data handling
    data_types_processed: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    sensitive_data_categories: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    processes_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    processes_health_data: Mapped[bool] = mapped_column(Boolean, default=False)
    processes_financial_data: Mapped[bool] = mapped_column(Boolean, default=False)
    processes_children_data: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI/ML usage
    uses_ai_ml: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_use_cases: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    ai_risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Applicable frameworks (explicit overrides)
    applicable_frameworks: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    excluded_frameworks: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Certifications and compliance status
    current_certifications: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    target_certifications: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)

    # Additional context
    business_processes: Mapped[list[str]] = mapped_column(ArrayType(String), default=list)
    third_party_vendors: Mapped[list[dict]] = mapped_column(JSONBType, default=list)
    custom_requirements: Mapped[list[dict]] = mapped_column(JSONBType, default=list)

    # Metadata
    settings: Mapped[dict] = mapped_column(JSONBType, default=dict)

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="customer_profiles"
    )
    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="customer_profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CustomerProfile {self.name}>"

    def get_applicable_frameworks(self) -> list[RegulatoryFramework]:
        """Determine applicable frameworks based on profile."""
        frameworks: set[str] = set()

        # Add explicit frameworks
        frameworks.update(self.applicable_frameworks)

        # Infer from jurisdictions
        for jurisdiction in self.operating_jurisdictions + self.customer_jurisdictions:
            if jurisdiction in ["eu", "uk"]:
                frameworks.add(RegulatoryFramework.GDPR.value)
            if jurisdiction == "uk":
                frameworks.add(RegulatoryFramework.UK_GDPR.value)
            if jurisdiction == "us_california":
                frameworks.add(RegulatoryFramework.CCPA.value)
                frameworks.add(RegulatoryFramework.CPRA.value)

        # Infer from data types
        if self.processes_health_data:
            frameworks.add(RegulatoryFramework.HIPAA.value)
        if self.processes_financial_data:
            frameworks.add(RegulatoryFramework.PCI_DSS.value)
            if self.is_publicly_traded:
                frameworks.add(RegulatoryFramework.SOX.value)

        # Infer from AI usage
        if self.uses_ai_ml and any(j in ["eu"] for j in self.operating_jurisdictions):
            frameworks.add(RegulatoryFramework.EU_AI_ACT.value)

        # Remove excluded
        frameworks -= set(self.excluded_frameworks)

        return [RegulatoryFramework(f) for f in frameworks if f in RegulatoryFramework.__members__]
