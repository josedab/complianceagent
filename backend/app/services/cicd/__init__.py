"""CI/CD compliance gate services."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.cicd.analyzer import CICDComplianceAnalyzer
from app.services.cicd.sarif import SARIFGenerator
from app.services.cicd.service import CICDComplianceService, CICDScanRequest, CICDScanResult


class Severity(str, Enum):
    """Compliance finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Finding:
    """A single compliance finding from a scan."""

    finding_id: str
    rule_id: str
    severity: Severity
    message: str
    file_path: str
    line_number: int
    regulation: str
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "severity": self.severity.value
            if isinstance(self.severity, Severity)
            else self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "regulation": self.regulation,
            "suggestion": self.suggestion,
        }


@dataclass
class ComplianceScanResult:
    """Result of a compliance scan with findings."""

    scan_id: str
    status: str
    total_files: int
    files_with_issues: int
    findings: list[Finding] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "status": self.status,
            "total_files": self.total_files,
            "files_with_issues": self.files_with_issues,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }


@dataclass
class SARIFReport:
    """SARIF v2.1.0 report structure."""

    version: str = "2.1.0"
    schema: str = ""
    runs: list[Any] = field(default_factory=list)

    def __post_init__(self):
        # Convert run dicts to SimpleNamespace for attribute access
        from types import SimpleNamespace

        self.runs = [
            SimpleNamespace(
                **{
                    k: (
                        [SimpleNamespace(**r) for r in v]
                        if k == "results" and isinstance(v, list)
                        else (SimpleNamespace(**v) if isinstance(v, dict) else v)
                    )
                    for k, v in r.items()
                }
            )
            if isinstance(r, dict)
            else r
            for r in self.runs
        ]


__all__ = [
    "CICDComplianceAnalyzer",
    "CICDComplianceService",
    "CICDScanRequest",
    "CICDScanResult",
    "ComplianceScanResult",
    "Finding",
    "SARIFGenerator",
    "SARIFReport",
    "Severity",
]
