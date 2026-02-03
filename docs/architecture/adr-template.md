# Architecture Decision Record (ADR) Template

Use this template when making significant architectural decisions for ComplianceAgent.

---

## ADR-XXX: [Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-YYY]

**Date:** YYYY-MM-DD

**Decision Makers:** [Names or roles]

**Technical Story:** [Link to issue/story if applicable]

---

## Context

[Describe the context and problem statement. What is the issue that is motivating this decision?]

### Requirements

- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

### Constraints

- [Constraint 1]
- [Constraint 2]

---

## Decision Drivers

- [Driver 1: e.g., Performance requirements]
- [Driver 2: e.g., Team expertise]
- [Driver 3: e.g., Cost considerations]
- [Driver 4: e.g., Time to market]

---

## Considered Options

### Option 1: [Name]

**Description:** [Brief description of this option]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Estimated Effort:** [Low | Medium | High]

### Option 2: [Name]

**Description:** [Brief description of this option]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Estimated Effort:** [Low | Medium | High]

### Option 3: [Name]

[Same structure as above]

---

## Decision

**Chosen Option:** [Option X]

**Rationale:** [Explain why this option was chosen. Reference decision drivers.]

---

## Consequences

### Positive

- [Positive consequence 1]
- [Positive consequence 2]

### Negative

- [Negative consequence 1]
- [Negative consequence 2]

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [How to mitigate] |
| [Risk 2] | Low/Med/High | Low/Med/High | [How to mitigate] |

---

## Implementation

### Tasks

- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | X weeks | [Description] |
| Phase 2 | X weeks | [Description] |

### Success Metrics

- [Metric 1: e.g., Latency < 100ms]
- [Metric 2: e.g., 99.9% availability]

---

## Related

- **Related ADRs:** [ADR-XXX, ADR-YYY]
- **Related Docs:** [Links to related documentation]
- **References:** [External references, articles, etc.]

---

## Notes

[Any additional notes, meeting outcomes, or follow-up items]

---

# Example ADRs

Below are the existing ADRs for ComplianceAgent. Use these as references.

## ADR-001: Use PostgreSQL for Primary Database

**Status:** Accepted

**Date:** 2024-01-15

### Context

We need a primary database for storing regulations, user data, compliance results, and audit logs. The system requires ACID compliance, complex queries, and JSON support.

### Decision

Use PostgreSQL 16 with async driver (asyncpg).

### Rationale

- Excellent JSON/JSONB support for flexible schemas
- Strong ACID compliance for audit requirements
- Native full-text search capabilities
- Team familiarity
- Excellent Python async support via asyncpg

### Consequences

- Need to manage PostgreSQL infrastructure
- Must implement connection pooling for scale

---

## ADR-002: Use FastAPI for Backend Framework

**Status:** Accepted

**Date:** 2024-01-15

### Context

We need a Python web framework for the REST API. Requirements include async support, automatic OpenAPI documentation, and strong typing.

### Decision

Use FastAPI with Pydantic for request/response validation.

### Rationale

- Native async/await support
- Automatic OpenAPI documentation
- Pydantic integration for validation
- High performance
- Large ecosystem

### Consequences

- Team needs to learn async Python patterns
- Dependency on Starlette for underlying ASGI

---

## ADR-003: Use GitHub Copilot SDK for AI Features

**Status:** Accepted

**Date:** 2024-01-20

### Context

The platform requires AI capabilities for legal text parsing, code analysis, and compliance recommendations. We need a reliable, production-ready AI service.

### Decision

Use GitHub Copilot SDK as the primary AI provider.

### Rationale

- Production-ready infrastructure
- Strong code understanding capabilities
- Existing GitHub integration
- Enterprise support available

### Consequences

- Vendor lock-in to GitHub/Microsoft
- API rate limits must be managed
- Cost scales with usage

---

## ADR-004: Multi-tenant Architecture with Organization Isolation

**Status:** Accepted

**Date:** 2024-02-01

### Context

The platform serves multiple organizations. Each organization's data must be isolated for security and compliance.

### Decision

Implement row-level multi-tenancy with organization_id on all tenant-specific tables.

### Rationale

- Simpler deployment than database-per-tenant
- Easier to query across tenants for platform analytics
- Cost-effective infrastructure

### Consequences

- Must ensure organization_id filter on ALL queries
- Need robust testing to prevent data leaks
- Index strategy must account for organization_id

---

## Creating New ADRs

1. Copy this template
2. Number sequentially (ADR-005, ADR-006, etc.)
3. Save as `docs/architecture/adr-XXX-title.md`
4. Update this index with a summary
5. Get review from relevant stakeholders
6. Update status when decision is made

---

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Use PostgreSQL for Primary Database | Accepted | 2024-01-15 |
| ADR-002 | Use FastAPI for Backend Framework | Accepted | 2024-01-15 |
| ADR-003 | Use GitHub Copilot SDK for AI Features | Accepted | 2024-01-20 |
| ADR-004 | Multi-tenant Architecture | Accepted | 2024-02-01 |
