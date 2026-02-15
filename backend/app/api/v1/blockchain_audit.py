"""API endpoints for Blockchain-Based Compliance Audit Trail."""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.deps import DB, CopilotDep
from app.services.blockchain_audit import BlockchainAuditService, BlockType


logger = structlog.get_logger()
router = APIRouter()


class AddBlockRequest(BaseModel):
    block_type: str
    data: dict


class AuditBlockSchema(BaseModel):
    id: str
    index: int
    block_type: str
    data: dict
    previous_hash: str
    hash: str
    timestamp: str
    nonce: int


class VerificationSchema(BaseModel):
    chain_length: int
    is_valid: bool
    invalid_blocks: list[int]
    verification_time_ms: float
    verified_at: str


class SmartContractRequest(BaseModel):
    name: str
    contract_type: str
    conditions: list[dict]
    auto_approve: bool = False


class SmartContractSchema(BaseModel):
    id: str
    name: str
    contract_type: str
    conditions: list[dict]
    auto_approve: bool
    created_at: str


class AuditProofSchema(BaseModel):
    block_index: int
    block_hash: str
    merkle_root: str
    merkle_proof: list[str]
    verified: bool


class BlockchainStateSchema(BaseModel):
    chain_length: int
    latest_hash: str
    is_valid: bool
    created_at: str


def _parse_block_type(bt: str) -> BlockType:
    try:
        return BlockType(bt)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid block type: {bt}. Use: {[t.value for t in BlockType]}"
        ) from None


def _block_to_schema(block) -> AuditBlockSchema:
    return AuditBlockSchema(
        id=str(block.id),
        index=block.index,
        block_type=block.block_type.value,
        data=block.data,
        previous_hash=block.previous_hash,
        hash=block.hash,
        timestamp=block.timestamp,
        nonce=block.nonce,
    )


@router.post("/blocks", response_model=AuditBlockSchema, summary="Add block to chain")
async def add_block(req: AddBlockRequest, db: DB, copilot: CopilotDep) -> AuditBlockSchema:
    bt = _parse_block_type(req.block_type)
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    block = await service.add_block(bt, req.data)
    return _block_to_schema(block)


@router.get("/chain", response_model=list[AuditBlockSchema], summary="Get full audit chain")
async def get_chain(db: DB, copilot: CopilotDep) -> list[AuditBlockSchema]:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    chain = await service.get_chain()
    return [_block_to_schema(b) for b in chain]


@router.get("/verify", response_model=VerificationSchema, summary="Verify chain integrity")
async def verify_chain(db: DB, copilot: CopilotDep) -> VerificationSchema:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    result = await service.verify_chain()
    return VerificationSchema(
        chain_length=result.chain_length,
        is_valid=result.is_valid,
        invalid_blocks=result.invalid_blocks,
        verification_time_ms=result.verification_time_ms,
        verified_at=result.verified_at,
    )


@router.get("/blocks/{index}", response_model=AuditBlockSchema, summary="Get block by index")
async def get_block(index: int, db: DB, copilot: CopilotDep) -> AuditBlockSchema:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    try:
        block = await service.get_block(index)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    return _block_to_schema(block)


@router.post(
    "/smart-contracts", response_model=SmartContractSchema, summary="Create smart contract"
)
async def create_smart_contract(
    req: SmartContractRequest, db: DB, copilot: CopilotDep
) -> SmartContractSchema:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    contract = await service.create_smart_contract(
        req.name,
        req.contract_type,
        req.conditions,
        req.auto_approve,
    )
    return SmartContractSchema(
        id=str(contract.id),
        name=contract.name,
        contract_type=contract.contract_type,
        conditions=contract.conditions,
        auto_approve=contract.auto_approve,
        created_at=contract.created_at,
    )


@router.get(
    "/smart-contracts", response_model=list[SmartContractSchema], summary="List smart contracts"
)
async def list_smart_contracts(db: DB, copilot: CopilotDep) -> list[SmartContractSchema]:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    contracts = await service.list_smart_contracts()
    return [
        SmartContractSchema(
            id=str(c.id),
            name=c.name,
            contract_type=c.contract_type,
            conditions=c.conditions,
            auto_approve=c.auto_approve,
            created_at=c.created_at,
        )
        for c in contracts
    ]


@router.get("/proof/{index}", response_model=AuditProofSchema, summary="Get audit proof")
async def get_audit_proof(index: int, db: DB, copilot: CopilotDep) -> AuditProofSchema:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    try:
        proof = await service.get_audit_proof(index)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    return AuditProofSchema(
        block_index=proof.block_index,
        block_hash=proof.block_hash,
        merkle_root=proof.merkle_root,
        merkle_proof=proof.merkle_proof,
        verified=proof.verified,
    )


@router.get("/state", response_model=BlockchainStateSchema, summary="Get blockchain state")
async def get_state(db: DB, copilot: CopilotDep) -> BlockchainStateSchema:
    service = BlockchainAuditService(db=db, copilot_client=copilot)
    state = await service.get_state()
    return BlockchainStateSchema(
        chain_length=state.chain_length,
        latest_hash=state.latest_hash,
        is_valid=state.is_valid,
        created_at=state.created_at,
    )
