"""Harmonization engine models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OverlapStrength(str, Enum):
    """Strength of overlap between controls."""

    exact = "exact"
    strong = "strong"
    moderate = "moderate"
    weak = "weak"


class ControlCategory(str, Enum):
    """Category of a compliance control."""

    access_control = "access_control"
    encryption = "encryption"
    logging = "logging"
    incident_response = "incident_response"
    data_protection = "data_protection"
    governance = "governance"


@dataclass
class FrameworkControl:
    """A single control from a compliance framework."""

    framework: str = ""
    control_id: str = ""
    control_name: str = ""
    category: ControlCategory = ControlCategory.access_control
    description: str = ""


@dataclass
class ControlOverlap:
    """Overlap between two controls from different frameworks."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    control_a: FrameworkControl = field(default_factory=FrameworkControl)
    control_b: FrameworkControl = field(default_factory=FrameworkControl)
    overlap_strength: OverlapStrength = OverlapStrength.moderate
    description: str = ""
    effort_savings_pct: float = 0.0


@dataclass
class HarmonizationResult:
    """Result of a framework harmonization analysis."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    frameworks: list[str] = field(default_factory=list)
    total_controls: int = 0
    unique_controls: int = 0
    overlapping_controls: int = 0
    deduplication_pct: float = 0.0
    overlaps: list[ControlOverlap] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class HarmonizationStats:
    """Aggregate statistics for harmonization analyses."""

    analyses_run: int = 0
    frameworks_analyzed: int = 0
    total_overlaps_found: int = 0
    avg_deduplication_pct: float = 0.0
    top_overlap_pairs: list[dict] = field(default_factory=list)
