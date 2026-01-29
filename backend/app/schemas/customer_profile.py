"""Customer profile schemas."""

from uuid import UUID

from pydantic import Field

from app.models.regulation import Jurisdiction
from app.schemas.base import BaseSchema, IDSchema, TimestampSchema


class CustomerProfileCreate(BaseSchema):
    """Schema for creating a customer profile."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_default: bool = False
    industry: str
    sub_industry: str | None = None
    company_size: str | None = None
    is_publicly_traded: bool = False
    headquarters_jurisdiction: Jurisdiction | None = None
    operating_jurisdictions: list[str] = Field(default_factory=list)
    customer_jurisdictions: list[str] = Field(default_factory=list)
    data_types_processed: list[str] = Field(default_factory=list)
    sensitive_data_categories: list[str] = Field(default_factory=list)
    processes_pii: bool = False
    processes_health_data: bool = False
    processes_financial_data: bool = False
    processes_children_data: bool = False
    uses_ai_ml: bool = False
    ai_use_cases: list[str] = Field(default_factory=list)
    ai_risk_level: str | None = None
    applicable_frameworks: list[str] = Field(default_factory=list)
    excluded_frameworks: list[str] = Field(default_factory=list)
    current_certifications: list[str] = Field(default_factory=list)
    target_certifications: list[str] = Field(default_factory=list)
    business_processes: list[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


class CustomerProfileUpdate(BaseSchema):
    """Schema for updating a customer profile."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_default: bool | None = None
    industry: str | None = None
    operating_jurisdictions: list[str] | None = None
    customer_jurisdictions: list[str] | None = None
    data_types_processed: list[str] | None = None
    processes_pii: bool | None = None
    processes_health_data: bool | None = None
    processes_financial_data: bool | None = None
    uses_ai_ml: bool | None = None
    ai_use_cases: list[str] | None = None
    applicable_frameworks: list[str] | None = None
    excluded_frameworks: list[str] | None = None
    settings: dict | None = None


class CustomerProfileRead(IDSchema, TimestampSchema):
    """Schema for reading a customer profile."""

    organization_id: UUID
    name: str
    description: str | None
    is_default: bool
    industry: str
    sub_industry: str | None
    company_size: str | None
    is_publicly_traded: bool
    headquarters_jurisdiction: Jurisdiction | None
    operating_jurisdictions: list[str]
    customer_jurisdictions: list[str]
    data_types_processed: list[str]
    sensitive_data_categories: list[str]
    processes_pii: bool
    processes_health_data: bool
    processes_financial_data: bool
    processes_children_data: bool
    uses_ai_ml: bool
    ai_use_cases: list[str]
    ai_risk_level: str | None
    applicable_frameworks: list[str]
    excluded_frameworks: list[str]
    current_certifications: list[str]
    target_certifications: list[str]
    settings: dict
    inferred_frameworks: list[str] = Field(default_factory=list)
