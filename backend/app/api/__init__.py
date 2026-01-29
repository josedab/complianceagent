"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    compliance,
    customer_profiles,
    mappings,
    organizations,
    regulations,
    repositories,
    requirements,
    users,
)


router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(
    customer_profiles.router, prefix="/customer-profiles", tags=["Customer Profiles"]
)
router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
router.include_router(mappings.router, prefix="/mappings", tags=["Codebase Mappings"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
