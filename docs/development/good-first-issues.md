# Good First Issues

> These issue descriptions are ready to be created on GitHub.
> Each is self-contained and suitable for new contributors.

---

## Issue 1: Add missing docstrings to core API routes

**Labels:** `good first issue`, `documentation`, `python`

**Description:**
Several API route handlers in `backend/app/api/v1/` are missing docstrings. FastAPI uses these docstrings to generate OpenAPI documentation, so adding them directly improves the API docs.

**Files to update:**
- `backend/app/api/v1/repositories.py`
- `backend/app/api/v1/compliance.py`
- `backend/app/api/v1/regulations.py`

**What to do:**
1. Open each file and find route handler functions (`@router.get`, `@router.post`, etc.)
2. Add a one-line docstring describing what the endpoint does
3. Run `make lint` to verify
4. Submit a PR

**Example:**
```python
@router.get("/")
async def list_regulations(...):
    """List all regulations with optional filtering by jurisdiction and framework."""
```

---

## Issue 2: Add type hints to seed script

**Labels:** `good first issue`, `python`, `enhancement`

**Description:**
The `scripts/seed.py` file lacks type annotations. Adding them improves code quality and IDE support.

**What to do:**
1. Add type hints to all function signatures in `scripts/seed.py`
2. Add return type annotations
3. Run `make type-check` to verify
4. Submit a PR

---

## Issue 3: Add loading skeletons to 3 dashboard pages

**Labels:** `good first issue`, `frontend`, `enhancement`

**Description:**
Several dashboard pages show a blank state while loading. Add the existing `Skeleton` component from `frontend/src/components/ui/Skeleton.tsx` to improve perceived performance.

**Files to update (pick any 3):**
- `frontend/src/app/dashboard/regulations/page.tsx`
- `frontend/src/app/dashboard/repositories/page.tsx`
- `frontend/src/app/dashboard/audit/page.tsx`

**What to do:**
1. Import the Skeleton component
2. Add a loading state that shows skeletons while data is being fetched
3. Run `npm run lint` and `npm run type-check` to verify

---

## Issue 4: Improve error messages in authentication

**Labels:** `good first issue`, `python`, `enhancement`

**Description:**
The auth endpoints in `backend/app/api/v1/auth.py` return generic error messages. Improve them to be more user-friendly while not leaking security details.

**What to do:**
1. Review error responses in `backend/app/api/v1/auth.py`
2. Make messages clearer (e.g., "Invalid email or password" instead of "401 Unauthorized")
3. Ensure no security-sensitive info is leaked
4. Add/update tests in `backend/tests/api/test_auth.py`

---

## Issue 5: Add ARIA labels to remaining UI components

**Labels:** `good first issue`, `frontend`, `accessibility`

**Description:**
The `frontend/src/components/ui/` directory has several components that need ARIA labels for screen reader accessibility.

**Components to improve:**
- `EmptyState.tsx` — add `role="status"` and `aria-label`
- `Toast.tsx` — add `role="alert"` and `aria-live="polite"`
- `CodeBlock.tsx` — add `aria-label` to copy button

**What to do:**
1. Open each component and add appropriate ARIA attributes
2. Test with a screen reader or browser accessibility inspector
3. Run `npm run lint` to verify

---

## Issue 6: Add unit tests for password validation

**Labels:** `good first issue`, `python`, `testing`

**Description:**
The security module at `backend/app/core/security.py` has password hashing but no edge case tests.

**What to do:**
1. Create `backend/tests/core/test_password_validation.py`
2. Test: empty password, very long password (1000+ chars), unicode characters, special characters
3. Verify password hash is not reversible
4. Run `make test-backend` to verify

---

## Issue 7: Document environment variables in .env.example

**Labels:** `good first issue`, `documentation`

**Description:**
Several newer environment variables mentioned in `backend/app/core/config.py` are missing from `.env.example`.

**What to do:**
1. Compare variables in `backend/app/core/config.py` with `.env.example`
2. Add any missing variables with descriptive comments
3. Ensure default values match between the two files
