# ADR-003: GitHub Copilot SDK for AI Operations

**Status:** Accepted

**Date:** 2024-01-20

**Decision Makers:** Engineering Team, AI/ML Lead

**Technical Story:** AI provider selection for legal text parsing, code mapping, and code generation

---

## Context

ComplianceAgent requires AI capabilities for legal text parsing, mapping regulations to code, and generating compliance code snippets. The AI integration must handle production realities including rate limits, service outages, and hallucination mitigation. The system needs structured, deterministic outputs from inherently probabilistic models.

### Requirements

- Parse and understand legal/regulatory text with high accuracy
- Map regulatory requirements to source code locations
- Generate compliance-related code snippets
- Handle API rate limits gracefully without dropping requests
- Recover from AI service outages without cascading failures
- Produce structured JSON outputs for downstream processing

### Constraints

- Must integrate with enterprise GitHub environments (SSO, org policies)
- AI costs must scale predictably with usage
- Responses must be structured and parseable, not free-form text

---

## Decision Drivers

- Alignment with existing GitHub-based development workflow
- Enterprise SSO and organization policy compatibility
- Quality of code generation and understanding
- Production reliability patterns (circuit breaker, retry)
- Structured output capabilities for deterministic processing

---

## Considered Options

### Option 1: GitHub Copilot SDK

**Description:** Use the GitHub Copilot SDK as the primary AI provider with circuit breaker, retry logic, and structured JSON prompting for all AI operations.

**Pros:**
- Native GitHub ecosystem alignment for code-centric workflows
- Enterprise SSO compatibility through GitHub organization policies
- Strong code generation and understanding quality
- SDK provides structured integration patterns
- Existing enterprise billing and usage tracking

**Cons:**
- Vendor lock-in to GitHub/Microsoft ecosystem
- API rate limits require careful management
- Less flexibility than direct model API access

**Estimated Effort:** Medium

### Option 2: OpenAI API (Direct)

**Description:** Direct integration with OpenAI's API (GPT-4, etc.) for all AI operations.

**Pros:**
- Most flexible model access and configuration
- Largest model selection (GPT-4, GPT-4 Turbo, etc.)
- Function calling and JSON mode support

**Cons:**
- No native GitHub integration; requires separate auth
- Enterprise SSO requires separate OpenAI organization setup
- Higher integration effort for code-specific workflows
- Cost management requires custom tracking

**Estimated Effort:** Medium

### Option 3: Anthropic Claude API

**Description:** Use Anthropic Claude for AI operations, particularly for legal text analysis.

**Pros:**
- Strong performance on legal and regulatory text
- Large context window for processing long documents
- Constitutional AI approach may reduce harmful outputs

**Cons:**
- No native GitHub ecosystem integration
- Smaller ecosystem of tools and integrations
- Enterprise features still maturing
- Separate authentication and billing infrastructure

**Estimated Effort:** Medium

### Option 4: Self-Hosted Models

**Description:** Deploy open-source models (LLaMA, Mistral) on own infrastructure.

**Pros:**
- Full control over model and data
- No vendor dependency or API rate limits
- Data never leaves the infrastructure

**Cons:**
- Significant GPU infrastructure cost
- Model quality may lag behind commercial options
- Operational burden of model serving and updates
- Longer time to production

**Estimated Effort:** High

---

## Decision

**Chosen Option:** Option 1 — GitHub Copilot SDK as primary AI provider with circuit breaker, retry logic, and structured JSON prompting.

**Rationale:** GitHub Copilot SDK provides the best alignment with the development workflow since ComplianceAgent operates within GitHub-centric environments. Enterprise SSO compatibility through GitHub organizations simplifies authentication. Code generation quality is strong for the code mapping and generation use cases. A circuit breaker pattern prevents cascading failures when the AI service is degraded, and structured JSON prompting ensures deterministic output parsing.

---

## Consequences

### Positive

- Seamless integration with GitHub enterprise environments and SSO
- Code understanding and generation tuned for development workflows
- Circuit breaker prevents AI outages from cascading to the rest of the platform
- Structured JSON prompting produces parseable, deterministic outputs
- Enterprise billing through existing GitHub contracts

### Negative

- Vendor lock-in to GitHub/Microsoft for AI capabilities
- API rate limits require queueing and backpressure mechanisms
- Cost scales with AI usage volume
- Model updates are controlled by GitHub, not the team

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI service outage | Medium | High | Circuit breaker with fallback to cached results; graceful degradation UI |
| Rate limit exhaustion | Medium | Medium | Request queueing with priority; exponential backoff; usage monitoring alerts |
| AI hallucination in legal text parsing | Medium | High | Structured JSON prompting with validation; human review workflow for critical outputs |
| Vendor lock-in limiting future options | Low | Medium | Abstract AI operations behind an interface; keep prompts model-agnostic where possible |

---

## Implementation

### Tasks

- [ ] Integrate GitHub Copilot SDK with backend service layer
- [ ] Implement circuit breaker pattern for AI API calls
- [ ] Implement retry logic with exponential backoff
- [ ] Design structured JSON prompt templates for each AI operation
- [ ] Add response validation layer for AI outputs
- [ ] Implement request queueing with priority for rate limit management
- [ ] Add monitoring and alerting for AI service health

### Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1 | 2 weeks | SDK integration, circuit breaker, and retry logic |
| Phase 2 | 2 weeks | Structured prompts and response validation |
| Phase 3 | 1 week | Monitoring, alerting, and rate limit management |

### Success Metrics

- AI service availability > 99.5% (measured at application layer with circuit breaker)
- Structured output parse success rate > 99%
- P95 AI response latency < 5 seconds
- Zero cascading failures from AI outages

---

## Related

- **Related ADRs:** ADR-001 (Technology Stack), ADR-005 (Service Module Pattern)
- **Related Docs:** [GitHub Copilot SDK Documentation](https://github.com/features/copilot)
- **References:** [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)

---

## Notes

The AI abstraction layer should be designed so that swapping to a different provider (OpenAI direct, Anthropic, or self-hosted) requires changes only in the adapter implementation, not in the business logic or prompt templates. This limits vendor lock-in risk while still leveraging GitHub Copilot SDK's strengths.
