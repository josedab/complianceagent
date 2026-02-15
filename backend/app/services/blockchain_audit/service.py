"""Blockchain-Based Compliance Audit Trail Service."""

import hashlib
import json
import time
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.blockchain_audit.models import (
    AuditBlock,
    AuditProof,
    BlockchainState,
    BlockType,
    SmartContract,
    VerificationResult,
)


logger = structlog.get_logger()


class BlockchainAuditService:
    """Immutable audit trail using blockchain-style hash chain."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._chain: list[AuditBlock] = []
        self._smart_contracts: dict[str, SmartContract] = {}
        self._init_genesis_block()

    def _init_genesis_block(self) -> None:
        """Create the genesis block."""
        genesis = AuditBlock(
            index=0,
            block_type=BlockType.AUDIT_EVENT,
            data={"event": "Genesis block — audit trail initialized"},
            previous_hash="0" * 64,
            timestamp=datetime.now(UTC).isoformat(),
            nonce=0,
        )
        genesis.hash = self._compute_hash(genesis)
        self._chain.append(genesis)

    def _compute_hash(self, block: AuditBlock) -> str:
        """Compute SHA-256 hash for a block."""
        block_content = json.dumps(
            {
                "index": block.index,
                "block_type": block.block_type.value,
                "data": block.data,
                "previous_hash": block.previous_hash,
                "timestamp": block.timestamp,
                "nonce": block.nonce,
            },
            sort_keys=True,
        )
        return hashlib.sha256(block_content.encode()).hexdigest()

    async def add_block(self, block_type: BlockType, data: dict) -> AuditBlock:
        """Add a new block to the chain."""
        previous_block = self._chain[-1]

        block = AuditBlock(
            index=len(self._chain),
            block_type=block_type,
            data=data,
            previous_hash=previous_block.hash,
            timestamp=datetime.now(UTC).isoformat(),
            nonce=0,
        )
        block.hash = self._compute_hash(block)
        self._chain.append(block)

        logger.info("Block added", index=block.index, type=block_type.value, hash=block.hash[:16])
        return block

    async def get_chain(self) -> list[AuditBlock]:
        """Get the full audit chain."""
        return list(self._chain)

    async def verify_chain(self) -> VerificationResult:
        """Verify the integrity of the entire chain."""
        start = time.monotonic()
        invalid_blocks: list[int] = []

        for i in range(1, len(self._chain)):
            block = self._chain[i]
            previous = self._chain[i - 1]

            # Verify hash
            computed = self._compute_hash(block)
            if computed != block.hash:
                invalid_blocks.append(block.index)

            # Verify chain link
            if block.previous_hash != previous.hash:
                invalid_blocks.append(block.index)

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)

        result = VerificationResult(
            chain_length=len(self._chain),
            is_valid=len(invalid_blocks) == 0,
            invalid_blocks=list(set(invalid_blocks)),
            verification_time_ms=elapsed_ms,
            verified_at=datetime.now(UTC).isoformat(),
        )
        logger.info("Chain verified", valid=result.is_valid, length=result.chain_length)
        return result

    async def get_block(self, index: int) -> AuditBlock:
        """Get a specific block by index."""
        if index < 0 or index >= len(self._chain):
            raise ValueError(f"Block index out of range: {index}. Chain length: {len(self._chain)}")
        return self._chain[index]

    async def create_smart_contract(
        self,
        name: str,
        contract_type: str,
        conditions: list[dict],
        auto_approve: bool,
    ) -> SmartContract:
        """Create a compliance smart contract."""
        contract = SmartContract(
            name=name,
            contract_type=contract_type,
            conditions=conditions,
            auto_approve=auto_approve,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._smart_contracts[str(contract.id)] = contract

        # Record contract creation on the chain
        await self.add_block(
            BlockType.COMPLIANCE_DECISION,
            {
                "event": "smart_contract_created",
                "contract_id": str(contract.id),
                "name": name,
                "contract_type": contract_type,
                "auto_approve": auto_approve,
            },
        )

        logger.info("Smart contract created", name=name, type=contract_type)
        return contract

    async def list_smart_contracts(self) -> list[SmartContract]:
        """List all smart contracts."""
        return list(self._smart_contracts.values())

    async def get_audit_proof(self, block_index: int) -> AuditProof:
        """Generate proof of a block's inclusion in the chain."""
        if block_index < 0 or block_index >= len(self._chain):
            raise ValueError(
                f"Block index out of range: {block_index}. Chain length: {len(self._chain)}"
            )

        block = self._chain[block_index]

        # Build simplified Merkle proof from chain hashes
        hashes = [b.hash for b in self._chain]
        merkle_root = self._compute_merkle_root(hashes)
        merkle_proof = self._build_merkle_proof(hashes, block_index)

        proof = AuditProof(
            block_index=block_index,
            block_hash=block.hash,
            merkle_root=merkle_root,
            merkle_proof=merkle_proof,
            verified=True,
        )
        return proof

    def _compute_merkle_root(self, hashes: list[str]) -> str:
        """Compute Merkle root from a list of hashes."""
        if not hashes:
            return hashlib.sha256(b"").hexdigest()
        if len(hashes) == 1:
            return hashes[0]

        current_level = list(hashes)
        while len(current_level) > 1:
            next_level: list[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            current_level = next_level
        return current_level[0]

    def _build_merkle_proof(self, hashes: list[str], index: int) -> list[str]:
        """Build a Merkle proof path for a specific index."""
        proof: list[str] = []
        current_level = list(hashes)

        idx = index
        while len(current_level) > 1:
            next_level: list[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                if i == idx or i + 1 == idx:
                    sibling = right if i == idx else left
                    proof.append(sibling)
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            idx = idx // 2
            current_level = next_level
        return proof

    async def get_state(self) -> BlockchainState:
        """Get current blockchain state."""
        verification = await self.verify_chain()
        return BlockchainState(
            chain_length=len(self._chain),
            latest_hash=self._chain[-1].hash if self._chain else "",
            is_valid=verification.is_valid,
            created_at=self._chain[0].timestamp if self._chain else "",
        )
