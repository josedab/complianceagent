# ADR-004: Hash Chain Audit Trail

**Status:** Accepted

**Date:** 2024-02-01

**Decision Makers:** Engineering Team, Security Lead, Compliance Officer

**Technical Story:** Tamper-proof audit logging for compliance verification

---

## Context

ComplianceAgent operates in a domain where regulatory compliance requires tamper-proof audit logs. Every action — regulation updates, compliance mappings, user decisions — must be recorded in a way that external auditors can independently verify has not been modified after the fact. The audit trail is a foundational requirement for the platform's credibility.

### Requirements

- Append-only audit log that detects tampering
- External auditors must be able to verify log integrity independently
- Audit entries must capture who, what, when, and organizational context
- Queryable log for operational use (filtering, searching, reporting)
- Reasonable storage and performance characteristics

### Constraints

- Must run within existing PostgreSQL infrastructure
- Verification must be possible without specialized tools
- Must not significantly degrade write performance for audited operations

---

## Decision Drivers

- Tamper detection is mandatory for compliance credibility
- Operational simplicity over cryptographic complexity
- Audit log must remain queryable with standard SQL
- External auditors need a simple verification mechanism
- Solution must work within existing infrastructure

---

## Considered Options

### Option 1: Hash Chain (SHA-256 Linked Entries)

**Description:** Each audit entry contains a SHA-256 hash computed from the previous entry's hash plus the current entry's data, forming an append-only chain. A verification endpoint allows auditors to walk the chain and confirm integrity.

**Pros:**
- Tamper detection without external dependencies
- Simple to implement and understand
- Stored in PostgreSQL — fully queryable with standard SQL
- Verification is a straightforward sequential hash check
- No additional infrastructure required

**Cons:**
- Verification is O(n) over the full chain
- If database admin alters entries and recomputes hashes, chain appears valid
- Single point of failure in the database

**Estimated Effort:** Low

### Option 2: Blockchain-Based Audit Log

**Description:** Record audit entries on a private blockchain (e.g., Hyperledger) for distributed tamper-proof storage.

**Pros:**
- Distributed consensus makes tampering extremely difficult
- Industry-recognized tamper-proof mechanism
- Immutable by design

**Cons:**
- Significant infrastructure complexity (nodes, consensus, networking)
- Slow write performance compared to database
- Querying is limited without additional indexing layers
- Overkill for a single-organization audit trail
- Team has no blockchain expertise

**Estimated Effort:** High

### Option 3: Append-Only Database Table

**Description:** Use PostgreSQL with table-level constraints to prevent UPDATE and DELETE on audit tables. Rely on database permissions for tamper prevention.

**Pros:**
- Simplest implementation
- Standard SQL for all operations
- No hash computation overhead

**Cons:**
- Database administrator can still modify or delete records
- No mechanism to detect tampering after the fact
- External auditors must trust database integrity entirely

**Estimated Effort:** Low

### Option 4: External Audit Service

**Description:** Send audit events to a third-party audit logging service (e.g., AWS CloudTrail, Drata, or a dedicated audit SaaS).

**Pros:**
- Purpose-built for compliance audit trails
- Tamper-proof guarantees by the provider
- Offloads storage and verification complexity

**Cons:**
- External dependency for a critical compliance feature
- Data sovereignty concerns with third-party storage
- Vendor lock-in and ongoing cost
- Latency for audit writes over network

**Estimated Effort:** Medium

---

## Decision

**Chosen Option:** Option 1 — Hash chain with SHA-256 linked entries stored in PostgreSQL.

**Rationale:** The hash chain provides tamper detection without blockchain complexity or external dependencies. Storing the chain in PostgreSQL keeps it queryable with standard SQL, which is essential for operational use. The verification endpoint gives external auditors a simple, independent way to confirm log integrity. The approach works within existing infrastructure and is straightforward to implement and maintain.

---

## Consequences

### Positive

- Tamper detection is built into the data structure itself
- Auditors can independently verify the chain via a REST endpoint
- Audit log remains queryable with standard SQL (filtering, reporting, search)
- No additional infrastructure beyond existing PostgreSQL
- Simple mental model: each entry is linked to the previous one via hash

### Negative

- Full chain verification is O(n) — may become slow for very large audit logs
- A compromised database admin could recompute the entire chain
- Hash computation adds a small overhead to every audited write

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Chain verification becomes slow at scale | Medium | Low | Periodic checkpoint hashes; parallel segment verification |
| Database admin recomputes hashes | Low | High | Periodic external hash snapshots; distribute chain root hash to auditors |
| Hash collision (SHA-256) | Negligible | High | SHA-256 is considered collision-resistant for the foreseeable future |
| Write performance degradation | Low | Low | Hash computation is fast (~microseconds); batch audit writes where appropriate |

---

## Implementation

### Tasks

- [ ] Create `audit_log` table with columns: id, timestamp, actor_id, organization_id, action, resource_type, resource_id, payload (JSONB), previous_hash, entry_hash
- [ ] Implement hash computation: `entry_hash = SHA-256(previous_hash + entry_data)`
- [ ] Create append-only service with transaction-level locking for chain consistency
- [ ] Build chain verification endpoint (`GET /api/v1/audit/verify`)
- [ ] Add periodic checkpoint hash export for external auditors
- [ ] Write integration tests for chain integrity under concurrent writes

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 1 week | Audit log table, hash chain computation, and append service |
| Phase 2 | 1 week | Verification endpoint and checkpoint export |
| Phase 3 | 1 week | Integration testing and performance benchmarking |

### Success Metrics

- Chain verification succeeds on 100% of audit log entries
- Audit write overhead < 5ms per entry
- Verification endpoint responds within 10 seconds for chains up to 1M entries
- Zero chain integrity failures in production

---

## Related

- **Related ADRs:** ADR-002 (Multi-Tenant Architecture), ADR-005 (Service Module Pattern)
- **Related Docs:** [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- **References:** [Hash Chain (Wikipedia)](https://en.wikipedia.org/wiki/Hash_chain), [Certificate Transparency](https://certificate.transparency.dev/)

---

## Notes

Consider publishing the chain's root hash periodically to an external, immutable store (e.g., a public git repository or a timestamping service) to guard against the scenario where a database admin recomputes the entire chain. This is not required for initial release but should be considered for high-assurance deployments.
