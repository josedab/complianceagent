# ADR-005: Service Module Pattern

**Status:** Accepted

**Date:** 2024-02-15

**Decision Makers:** Engineering Team

**Technical Story:** Codebase organization pattern for 100+ features

---

## Context

ComplianceAgent is expected to grow to 100+ features covering regulation tracking, code mapping, audit trails, reporting, and more. The codebase needs a consistent organizational pattern that supports independent development and testing across features without fragmenting into separate deployable units prematurely. Each feature must have clear boundaries and ownership.

### Requirements

- Consistent directory structure across all features
- Independent development and testing per feature
- Clear separation between internal models and API contracts
- Single deployable unit (monolith) for operational simplicity
- Easy onboarding — new developers can understand the pattern quickly

### Constraints

- Must work within a single Python package and deployment
- Must integrate with FastAPI's router registration pattern
- Internal models and API models must remain distinct

---

## Decision Drivers

- Codebase maintainability as feature count grows beyond 100
- Clear ownership boundaries per feature for parallel development
- Independent testability without full application bootstrap
- Consistent patterns that reduce cognitive load for developers
- Single deployment unit to avoid premature microservice complexity

---

## Considered Options

### Option 1: Service Module Pattern (Module-per-Feature)

**Description:** Each feature gets a `services/{name}/` directory containing `__init__.py`, `models.py` (Python dataclasses for internal models), and `service.py` (business logic). API routes live in `api/v1/{name}.py` using Pydantic models for request/response schemas. Each service is registered in `api/v1/__init__.py`.

**Pros:**
- Consistent, predictable directory structure for every feature
- Dataclasses for internal models decouple business logic from API layer
- Pydantic models at API boundaries provide validation and documentation
- Each service is independently testable
- Single deployment unit keeps operations simple
- New features follow a clear template

**Cons:**
- Some boilerplate per feature (init, models, service files)
- Cross-feature dependencies need explicit imports
- Single deployment means all features share the same release cycle

**Estimated Effort:** Low

### Option 2: Monolithic Service Layer

**Description:** A single `services/` module with all business logic in a flat structure. Models and services share the same namespace.

**Pros:**
- Minimal boilerplate
- Simple imports between features

**Cons:**
- Becomes unwieldy beyond 20-30 features
- No clear ownership boundaries
- Hard to test features in isolation
- Merge conflicts increase as team grows

**Estimated Effort:** Low

### Option 3: Microservices

**Description:** Each feature is a separate deployable service with its own API, database schema, and deployment pipeline.

**Pros:**
- Complete independence between features
- Independent scaling and deployment per feature
- Technology diversity possible per service

**Cons:**
- Massive operational overhead for 100+ services
- Distributed transaction complexity
- Inter-service communication latency
- Premature for current team size and maturity

**Estimated Effort:** High

### Option 4: Hexagonal Architecture (Ports and Adapters)

**Description:** Organize code around ports (interfaces) and adapters (implementations) with strict layering between domain, application, and infrastructure.

**Pros:**
- Strong architectural boundaries
- Technology-agnostic domain layer
- Highly testable with mock adapters

**Cons:**
- Significant boilerplate and abstraction overhead
- Steep learning curve for team members
- Over-engineered for many CRUD-heavy features
- Python's duck typing makes strict interfaces less natural

**Estimated Effort:** High

---

## Decision

**Chosen Option:** Option 1 — Service Module Pattern with `services/{name}/` directories, dataclass internal models, Pydantic API models, and centralized route registration.

**Rationale:** The module-per-feature pattern provides clear ownership and independent testability while staying in a single deployable unit. Dataclasses for internal models keep business logic free from API serialization concerns, while Pydantic models at API boundaries provide automatic validation and OpenAPI documentation. The pattern scales to 100+ features with consistent structure and minimal cognitive load for new developers.

---

## Consequences

### Positive

- Every feature follows the same directory and file structure
- Business logic in `service.py` is testable without FastAPI or HTTP
- Pydantic models at API boundaries ensure validation and auto-documentation
- Dataclasses keep internal models lightweight and framework-independent
- New features can be scaffolded from a template
- Code reviews benefit from predictable structure

### Negative

- Boilerplate for each new feature (3+ files minimum)
- Cross-feature dependencies require explicit imports and may create coupling
- All features share the same deployment — a bug in one feature affects all

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Cross-feature coupling through shared models | Medium | Medium | Code review guidelines; lint rules for import boundaries |
| Boilerplate fatigue | Low | Low | Feature scaffolding script or template |
| Single deployment blast radius | Medium | Medium | Feature flags; canary deployments; comprehensive test coverage |

---

## Implementation

### Tasks

- [ ] Create `services/` directory with initial feature modules
- [ ] Define `models.py` template using Python dataclasses
- [ ] Define `service.py` template with standard method signatures
- [ ] Create `api/v1/{name}.py` route template using Pydantic models
- [ ] Implement centralized route registration in `api/v1/__init__.py`
- [ ] Write feature scaffolding script for new modules
- [ ] Document the pattern in developer guide

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 1 week | Directory structure, templates, and first 3 feature modules |
| Phase 2 | 1 week | Scaffolding script and developer documentation |
| Phase 3 | Ongoing | Apply pattern as new features are added |

### Success Metrics

- 100% of features follow the module pattern
- New feature scaffolding takes < 5 minutes
- Unit tests for service layer run without FastAPI bootstrap
- Developer onboarding time for pattern understanding < 1 hour

---

## Related

- **Related ADRs:** ADR-001 (Technology Stack), ADR-002 (Multi-Tenant Architecture), ADR-003 (GitHub Copilot SDK)
- **Related Docs:** [FastAPI Router Documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- **References:** [Python Dataclasses](https://docs.python.org/3/library/dataclasses.html), [Pydantic Models](https://docs.pydantic.dev/latest/)

---

## Notes

The directory structure for a typical feature module:

```
services/
  regulations/
    __init__.py
    models.py       # Python dataclasses for internal domain models
    service.py      # Business logic (no framework dependencies)
api/
  v1/
    __init__.py     # Router registration for all features
    regulations.py  # FastAPI routes with Pydantic request/response models
```

This pattern intentionally keeps internal models (dataclasses) separate from API models (Pydantic) to allow the business logic to evolve independently from the API contract.
