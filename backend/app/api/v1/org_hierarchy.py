"""API endpoints for Multi-Tenant Organization Hierarchy."""

from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.org_hierarchy import OrgHierarchyService, OrgNodeType, OrgRole

logger = structlog.get_logger()
router = APIRouter()


class CreateNodeRequest(BaseModel):
    name: str = Field(..., min_length=1)
    node_type: str = Field(default="team")
    parent_id: str | None = Field(default=None)
    slug: str | None = Field(default=None)
    policies: dict = Field(default_factory=dict)


class AddMemberRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    user_email: str = Field(...)
    role: str = Field(default="viewer")


class NodeSchema(BaseModel):
    id: str
    name: str
    slug: str
    node_type: str
    parent_id: str | None
    depth: int
    policy_inheritance: str


class MemberSchema(BaseModel):
    id: str
    user_email: str
    role: str
    inherited_roles: list[str]


@router.post("/nodes", response_model=NodeSchema, status_code=status.HTTP_201_CREATED, summary="Create org node")
async def create_node(request: CreateNodeRequest, db: DB, copilot: CopilotDep) -> NodeSchema:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    try:
        nt = OrgNodeType(request.node_type)
    except ValueError:
        nt = OrgNodeType.TEAM
    parent = UUID(request.parent_id) if request.parent_id else None
    try:
        node = await service.create_node(name=request.name, node_type=nt, parent_id=parent,
                                          slug=request.slug, policies=request.policies)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return NodeSchema(id=str(node.id), name=node.name, slug=node.slug, node_type=node.node_type.value,
                      parent_id=str(node.parent_id) if node.parent_id else None,
                      depth=node.depth, policy_inheritance=node.policy_inheritance.value)


@router.get("/tree", summary="Get organization tree")
async def get_tree(db: DB, copilot: CopilotDep, root_id: str | None = None) -> dict:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    rid = UUID(root_id) if root_id else None
    tree = await service.get_tree(root_id=rid)
    return {
        "root": {"id": str(tree.root.id), "name": tree.root.name} if tree.root else None,
        "total_nodes": len(tree.nodes), "total_members": tree.total_members, "max_depth": tree.max_depth,
        "nodes": [{"id": str(n.id), "name": n.name, "type": n.node_type.value, "depth": n.depth,
                    "parent_id": str(n.parent_id) if n.parent_id else None} for n in tree.nodes],
    }


@router.post("/nodes/{node_id}/members", response_model=MemberSchema, status_code=status.HTTP_201_CREATED,
             summary="Add member to node")
async def add_member(node_id: str, request: AddMemberRequest, db: DB, copilot: CopilotDep) -> MemberSchema:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    try:
        role = OrgRole(request.role)
    except ValueError:
        role = OrgRole.VIEWER
    try:
        member = await service.add_member(user_id=UUID(request.user_id), user_email=request.user_email,
                                           org_node_id=UUID(node_id), role=role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MemberSchema(id=str(member.id), user_email=member.user_email, role=member.role.value,
                        inherited_roles=[r.value for r in member.inherited_roles])


@router.get("/nodes/{node_id}/members", response_model=list[MemberSchema], summary="Get node members")
async def get_members(node_id: str, db: DB, copilot: CopilotDep, include_inherited: bool = True) -> list[MemberSchema]:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    members = await service.get_members(UUID(node_id), include_inherited=include_inherited)
    return [MemberSchema(id=str(m.id), user_email=m.user_email, role=m.role.value,
                          inherited_roles=[r.value for r in m.inherited_roles]) for m in members]


@router.get("/nodes/{node_id}/policies", summary="Get effective policies for node")
async def get_policies(node_id: str, db: DB, copilot: CopilotDep) -> dict:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    return await service.get_effective_policies(UUID(node_id))


@router.get("/nodes/{node_id}/compliance", summary="Get aggregated compliance for node")
async def get_compliance(node_id: str, db: DB, copilot: CopilotDep) -> dict:
    service = OrgHierarchyService(db=db, copilot_client=copilot)
    try:
        agg = await service.get_aggregated_compliance(UUID(node_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "org_node_name": agg.org_node_name, "overall_score": agg.overall_score,
        "children_scores": agg.children_scores, "violation_count": agg.violation_count,
        "repository_count": agg.repository_count,
    }
