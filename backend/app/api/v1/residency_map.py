"""Data Residency Map API endpoints."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.residency_map import ResidencyMapService


logger = structlog.get_logger()
router = APIRouter()


class TransferCheckRequest(BaseModel):
    source: str = Field(..., description="Source jurisdiction code (e.g., EU, US)")
    destination: str = Field(..., description="Destination jurisdiction code")
    data_types: list[str] = Field(default_factory=lambda: ["personal_data"])


@router.get("/report")
async def get_residency_report(db: DB) -> dict:
    """Get data residency report showing all cross-border data flows."""
    svc = ResidencyMapService(db)
    report = await svc.get_residency_report()
    return {
        "total_flows": report.total_flows,
        "compliant": report.compliant,
        "violations": report.violations,
        "review_needed": report.review_needed,
        "jurisdictions_involved": report.jurisdictions_involved,
        "flows": [
            {
                "id": str(f.id),
                "source": f.source_jurisdiction,
                "destination": f.destination_jurisdiction,
                "data_types": f.data_types,
                "service": f.service_name,
                "transfer_mechanism": f.transfer_mechanism,
                "status": f.status.value,
                "violations": f.violations,
            }
            for f in report.flows
        ],
    }


@router.post("/check-transfer")
async def check_transfer(request: TransferCheckRequest, db: DB) -> dict:
    """Check if a specific cross-border data transfer is compliant."""
    svc = ResidencyMapService(db)
    flow = await svc.check_transfer(request.source, request.destination, request.data_types)
    return {
        "source": flow.source_jurisdiction,
        "destination": flow.destination_jurisdiction,
        "status": flow.status.value,
        "violations": flow.violations,
        "data_types": flow.data_types,
    }


@router.get("/jurisdictions")
async def list_jurisdictions(db: DB) -> list[dict]:
    """List all known jurisdictions and their applicable laws."""
    svc = ResidencyMapService(db)
    jurisdictions = await svc.get_jurisdictions()
    return [
        {
            "code": j.code,
            "name": j.name,
            "region": j.region,
            "applicable_laws": j.applicable_laws,
            "adequacy_decisions": j.adequacy_decisions,
            "requires_local_storage": j.requires_local_storage,
        }
        for j in jurisdictions
    ]


@router.get("/resolve-region")
async def resolve_cloud_region(
    region: str = Query(..., description="Cloud region (e.g., us-east-1, eu-west-1)"),
    db: DB = None,
) -> dict:
    """Map a cloud region to its data residency jurisdiction."""
    svc = ResidencyMapService(db)
    jurisdiction = await svc.resolve_cloud_region(region)
    return {"region": region, "jurisdiction": jurisdiction}
