# ADR-001: FastAPI + Next.js Technology Stack

**Status:** Accepted

**Date:** 2024-01-15

**Decision Makers:** Engineering Team

**Technical Story:** Full-stack platform selection for ComplianceAgent

---

## Context

ComplianceAgent requires a full-stack platform for compliance automation. The backend needs async I/O for crawling regulatory sources, strong typing for data integrity, and automatic OpenAPI documentation for API consumers. The frontend needs server-side rendering for SEO and performance, TypeScript for type safety, and modern React patterns for building accessible, maintainable UI components.

### Requirements

- Async I/O support for concurrent regulatory source crawling
- Automatic OpenAPI spec generation for API documentation
- Strong request/response validation with type safety
- Server-side rendering for frontend performance and SEO
- TypeScript support across the frontend codebase
- Accessible UI component primitives

### Constraints

- Team has primary expertise in Python and TypeScript
- Must integrate with AI/NLP libraries in the Python ecosystem
- Must support enterprise-grade authentication flows

---

## Decision Drivers

- Async-first architecture for I/O-bound regulatory crawling workloads
- Python's dominant NLP and AI library ecosystem
- Type safety across both frontend and backend
- Automatic API documentation generation
- Time to market with proven frameworks

---

## Considered Options

### Option 1: FastAPI (Python) + Next.js (TypeScript)

**Description:** Python 3.12+ with FastAPI for the backend REST API; Next.js 14 with TypeScript and Radix UI for the frontend.

**Pros:**
- FastAPI's async-first model is ideal for regulatory source crawling
- Automatic OpenAPI generation from Pydantic models
- Pydantic provides strong runtime validation
- Python ecosystem gives direct access to NLP/AI libraries
- Next.js App Router provides SSR, streaming, and React Server Components
- Radix UI primitives deliver accessible components out of the box

**Cons:**
- Two language ecosystems to maintain (Python + TypeScript)
- Deployment requires separate backend and frontend services

**Estimated Effort:** Medium

### Option 2: Django REST Framework + React SPA

**Description:** Django with DRF for the backend; Create React App or Vite for the frontend.

**Pros:**
- Django's mature ORM and admin interface
- Large community and extensive documentation
- DRF provides serialization and viewsets

**Cons:**
- Django is synchronous by default; async support is still maturing
- No automatic OpenAPI generation without additional packages
- React SPA lacks built-in SSR
- Heavier framework with more boilerplate

**Estimated Effort:** Medium

### Option 3: Flask + React SPA

**Description:** Flask with extensions for the backend; React SPA for the frontend.

**Pros:**
- Lightweight and flexible
- Simple to get started

**Cons:**
- No built-in async support
- No native validation or OpenAPI generation
- Requires many extensions to match FastAPI's built-in features
- React SPA lacks SSR

**Estimated Effort:** Medium

### Option 4: Express.js + React

**Description:** Node.js with Express for the backend; React for the frontend.

**Pros:**
- Single language (JavaScript/TypeScript) across the stack
- Large npm ecosystem

**Cons:**
- Loses access to Python's NLP/AI library ecosystem
- No built-in validation or OpenAPI generation
- Would require Python microservices for AI workloads anyway

**Estimated Effort:** High

### Option 5: Go Backend + React

**Description:** Go with Gin or Echo for the backend; React for the frontend.

**Pros:**
- Excellent performance and concurrency model
- Strong typing and compiled binaries

**Cons:**
- Limited NLP/AI library ecosystem
- Team lacks Go expertise
- Would require Python microservices for AI workloads
- Higher development time for CRUD operations

**Estimated Effort:** High

---

## Decision

**Chosen Option:** Option 1 — FastAPI (Python 3.12+) + Next.js 14 (TypeScript)

**Rationale:** FastAPI's async-first model is the best fit for regulatory source crawling workloads that are heavily I/O-bound. Automatic OpenAPI generation from Pydantic models eliminates documentation drift. Python's ecosystem provides direct access to NLP and AI libraries critical for legal text parsing. Next.js 14's App Router delivers SSR, type safety via TypeScript, and Radix UI primitives for building accessible compliance dashboards.

---

## Consequences

### Positive

- Async crawling of regulatory sources with high concurrency
- OpenAPI documentation stays in sync with code automatically
- Pydantic models enforce validation at API boundaries
- Access to the full Python AI/NLP ecosystem without bridging languages
- SSR improves initial load performance and SEO for public-facing pages
- TypeScript catches frontend errors at compile time

### Negative

- Two language ecosystems require broader team skills
- Separate deployment pipelines for backend and frontend
- Pydantic v2 migration may be needed as ecosystem evolves

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FastAPI ecosystem churn | Low | Medium | Pin dependency versions; monitor changelogs |
| Next.js App Router breaking changes | Medium | Medium | Pin Next.js version; upgrade on a planned cadence |
| Team context-switching between Python and TypeScript | Low | Low | Clear code ownership boundaries per service |

---

## Implementation

### Tasks

- [ ] Initialize FastAPI backend project with Python 3.12+
- [ ] Configure Pydantic v2 models and OpenAPI generation
- [ ] Initialize Next.js 14 frontend with TypeScript and App Router
- [ ] Integrate Radix UI component primitives
- [ ] Set up shared API types between backend OpenAPI spec and frontend

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2 weeks | Backend and frontend project scaffolding |
| Phase 2 | 2 weeks | Core API endpoints and frontend pages |
| Phase 3 | 1 week | Integration testing and deployment pipeline |

### Success Metrics

- API response latency < 200ms for standard CRUD operations
- Lighthouse performance score > 90 for frontend pages
- 100% of API endpoints documented via auto-generated OpenAPI spec

---

## Related

- **Related ADRs:** ADR-002 (Multi-Tenant Architecture), ADR-005 (Service Module Pattern)
- **Related Docs:** [FastAPI Documentation](https://fastapi.tiangolo.com/), [Next.js Documentation](https://nextjs.org/docs)
- **References:** [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)

---

## Notes

Python 3.12+ chosen specifically for performance improvements in the interpreter and improved error messages. Next.js 14 chosen for stable App Router and React Server Components support.
