# ADR-002: Multi-Tenant Organization Architecture

**Status:** Accepted

**Date:** 2024-02-01

**Decision Makers:** Engineering Team, Security Lead

**Technical Story:** Organization isolation and RBAC for multi-tenant platform

---

## Context

ComplianceAgent serves multiple organizations that must have strictly isolated data. Each organization manages its own regulations, compliance mappings, and audit trails. The platform needs role-based access control (RBAC) with organizational hierarchy support. Data leakage between tenants is a critical compliance violation.

### Requirements

- Complete data isolation between organizations
- Role-based access control within each organization
- Organizational hierarchy (org → teams → users)
- JWT-based authentication carrying organization context
- Scalable to thousands of tenants without infrastructure changes

### Constraints

- Single PostgreSQL cluster for operational simplicity
- Must support cross-tenant platform analytics for system administrators
- Audit trail must capture organization context for every operation

---

## Decision Drivers

- Operational simplicity of a single database deployment
- Cost-effective scaling to thousands of tenants
- Strong data isolation guarantees for compliance requirements
- Team familiarity with relational database patterns
- Need for cross-tenant analytics and reporting

---

## Considered Options

### Option 1: Row-Level Multi-Tenancy with organization_id

**Description:** Every tenant-scoped table includes an `organization_id` foreign key column. All queries filter by `organization_id`. JWT tokens carry an `org_id` claim for request-scoped tenant identification.

**Pros:**
- Simple to implement and operate with a single database
- Scales to thousands of tenants without infrastructure changes
- Cross-tenant analytics queries are straightforward
- PostgreSQL Row-Level Security (RLS) available for enforcement
- Standard migration and backup tooling applies uniformly

**Cons:**
- Every query must include `organization_id` filter — risk of accidental omission
- Noisy neighbor potential under heavy load from a single tenant
- All tenant data shares the same backup/restore lifecycle

**Estimated Effort:** Low

### Option 2: Separate Database per Tenant

**Description:** Each organization gets its own PostgreSQL database instance. Routing layer directs requests to the appropriate database.

**Pros:**
- Complete physical isolation between tenants
- Independent backup and restore per tenant
- No risk of query-level data leakage

**Cons:**
- Operational complexity scales linearly with tenant count
- Cross-tenant analytics requires federation or ETL
- Connection pooling becomes complex with hundreds of databases
- Higher infrastructure cost

**Estimated Effort:** High

### Option 3: Schema-per-Tenant

**Description:** Each organization gets a separate PostgreSQL schema within the same database. Application layer sets `search_path` per request.

**Pros:**
- Good isolation within a single database
- Independent schema migrations possible per tenant

**Cons:**
- Schema migrations must be applied to every tenant schema
- PostgreSQL has practical limits on schema count
- Tooling and ORM support for dynamic schemas is limited
- Cross-tenant queries require explicit schema references

**Estimated Effort:** Medium

---

## Decision

**Chosen Option:** Option 1 — Row-level multi-tenancy with `organization_id` foreign key on all tenant-scoped tables. JWT tokens carry `org_id` claim.

**Rationale:** Row-level multi-tenancy is the simplest approach to operate and scales to thousands of tenants without infrastructure changes. PostgreSQL RLS provides a database-level enforcement layer as a safety net. Cross-tenant platform analytics remain straightforward with a single schema. The team can implement and test this pattern quickly with existing tooling.

---

## Consequences

### Positive

- Single database simplifies deployment, backups, and monitoring
- Standard SQL queries with `WHERE organization_id = :org_id` are easy to audit
- PostgreSQL RLS adds a defense-in-depth layer against accidental data leakage
- Cross-tenant reporting and analytics work without ETL pipelines
- New tenants onboard instantly without infrastructure provisioning

### Negative

- Every tenant-scoped query must include `organization_id` — requires discipline and code review
- Noisy neighbor risk requires query-level rate limiting or resource quotas
- Single backup lifecycle means tenant-specific restore is complex

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Accidental omission of organization_id filter | Medium | High | PostgreSQL RLS policies; mandatory middleware injection; automated query analysis in tests |
| Noisy neighbor degrading performance | Low | Medium | Per-tenant rate limiting; query timeout enforcement; connection pool limits |
| Data leakage through cross-tenant joins | Low | High | Code review checklist; integration tests with multi-tenant fixtures |

---

## Implementation

### Tasks

- [ ] Add `organization_id` column to all tenant-scoped tables
- [ ] Create PostgreSQL RLS policies for tenant isolation enforcement
- [ ] Implement middleware to extract `org_id` from JWT and inject into query context
- [ ] Add RBAC models (roles, permissions) scoped to organization
- [ ] Write integration tests verifying cross-tenant isolation
- [ ] Add composite indexes on `(organization_id, ...)` for query performance

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2 weeks | Schema changes and RLS policy implementation |
| Phase 2 | 2 weeks | Middleware, RBAC models, and JWT integration |
| Phase 3 | 1 week | Integration testing and security review |

### Success Metrics

- Zero cross-tenant data leakage in integration test suite
- Query performance within 10% of single-tenant baseline
- New tenant onboarding completes in < 1 second (no provisioning)

---

## Related

- **Related ADRs:** ADR-001 (Technology Stack), ADR-004 (Hash Chain Audit Trail)
- **Related Docs:** [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- **References:** [Multi-tenant SaaS Patterns](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models)

---

## Notes

PostgreSQL RLS policies should be treated as a safety net, not the primary enforcement mechanism. The application layer must always filter by `organization_id` explicitly. RLS catches omissions as a defense-in-depth measure.
