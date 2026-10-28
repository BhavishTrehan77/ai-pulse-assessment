# AI Pulse

AI Pulse helps companies understand how well employees use AI at work and identify AI-maturity and usage risks across an organization.

Employees sign in, select an organization, and complete a diagnostic whose questions adapt to their job role and seniority. Each employee receives a personal report containing a maturity level, identified risks, and role-based next steps. Company admins can view department-level maturity and risks.

The application also supports users who belong to multiple organizations.

## Assessment Context

This repository was inherited in a working but untrusted state. I reviewed the existing implementation, identified authorization, privacy, validation, security, and reliability issues, implemented the requested client changes, and added one employee-facing feature.

## Stack

- Backend: Python, FastAPI, SQLAlchemy
- Database: SQLite by default
- Frontend: React + Vite
- AI: OpenAI-compatible chat completions endpoint with mock mode for local development
- Testing: pytest

## Client Requests

The client requested two changes before rollout:

1. **Small-group privacy:** if fewer than 5 people in a department have completed the diagnostic, leadership must not see that department's scores or risks individually.
2. **Right to delete:** employees must be able to delete their diagnostic answers and report data themselves, with deletion correctly scoped for users who belong to multiple organizations.

Both requests were implemented and covered by tests.

---

# What I Found and Fixed

## 1. Organization authorization

The dashboard could be requested with an organization ID without sufficiently verifying that the authenticated user belonged to that organization.

I added server-side organization membership checks so a user cannot access another organization's dashboard.

I also fixed organization selection so a user cannot request a token for an organization they do not belong to.

## 2. Seniority filtering

The diagnostic question filtering compared seniority values as strings instead of using their actual hierarchy.

I replaced that behavior with an explicit ordered mapping:

```python
SENIORITY_LEVELS = {
    "junior": 0,
    "mid": 1,
    "senior": 2,
    "lead": 3,
}
```

This makes question eligibility depend on the actual seniority order.

## 3. Small-group dashboard privacy

Department results are now based on the number of employees who have actually responded to the diagnostic.

Departments with fewer than 5 respondents are hidden from the dashboard.

I chose the "hide the department" option allowed by the client request rather than aggregating small groups into an "Other teams" bucket. This keeps the privacy rule simple and reduces the chance of accidentally exposing a small group's results.

## 4. Department average calculation

The original dashboard average divided the total scores by the number of department members.

The calculation was corrected to use the number of available scores instead, so the average reflects the responses that actually contributed scores.

## 5. Right to delete

Employees can delete their diagnostic data through:

```text
DELETE /reports/me
```

Deletion is scoped to the employee's **current organization membership**, not globally to the user.

This matters because a single user can belong to multiple organizations. Deleting data for one organization therefore does not remove the user's diagnostic data from another organization.

The report is derived from response data, so removing those responses also removes the underlying data used by the employee's report.

## 6. Diagnostic input validation

Diagnostic submissions now validate that:

- submitted question IDs belong to the employee's assigned diagnostic
- duplicate question IDs are rejected
- MCQ answers contain valid options
- validation happens before response records are persisted

This prevents clients from submitting arbitrary questions or malformed answers.

## 7. AI output validation

LLM output is treated as untrusted input.

The scoring layer validates:

- valid JSON
- object structure
- integer score
- score range of 1–5
- non-empty reason
- flags are represented as a list
- flags contain strings
- flags use only the supported risk labels

Invalid AI output is rejected instead of being stored blindly.

The diagnostic endpoint converts invalid AI scoring output into a controlled `502` response.

## 8. Mock AI fixture reliability

The inherited mock AI fixture contained both valid responses and intentionally malformed responses.

The mock provider randomly selected from that same pool during normal diagnostic submissions, which meant a normal submission could receive a deliberately invalid test response and fail.

I separated the valid runtime mock responses from malformed-output cases used by validation tests.

The strict AI validation remains in place; only the runtime mock data was cleaned up.

## 9. Password security

The original application used SHA-256 for password storage.

New password hashes now use Argon2 through `pwdlib`.

Existing SHA-256 hashes remain temporarily verifiable for backward compatibility. After a successful login, a legacy SHA-256 password is upgraded to Argon2.

This allows gradual migration without requiring every existing user to reset their password immediately.

## 10. JWT secret hardening

The original configuration had a predictable hard-coded fallback JWT secret.

Production now requires `SECRET_KEY` to be supplied through configuration and requires it to meet a minimum length.

For local development, an ephemeral random secret is used when one is not supplied, rather than a predictable hard-coded secret.

## 11. CORS hardening

The original configuration allowed all origins:

```python
allow_origins=["*"]
```

Allowed frontend origins are now configured through `CORS_ORIGINS`.

The local default is the Vite development origin:

```text
http://localhost:5173
```

Production deployments can provide their approved frontend origins through configuration.

---

# Own Feature: Personal AI Action Plan

I added a **Personal AI Action Plan** to the employee report.

The diagnostic already produces structured risk flags. The new feature maps those detected risks to concrete remediation actions.

Examples include:

- `customer_data_shared` → guidance for protecting customer data
- `confidential_data_shared` → guidance for protecting confidential information
- `unreviewed_output` → guidance to review AI-generated output
- `policy_unaware` → guidance to review the organization's AI usage policy

## Why I chose this feature

The diagnostic already contains structured risk information, so another LLM call would add unnecessary complexity and another source of uncertainty.

Instead, the feature uses a deterministic mapping from validated risk → recommended action.

That gives the feature:

- predictable behavior
- easy testing
- traceability from risk to recommendation
- no additional AI failure point
- simple maintenance

It also fits naturally into the existing employee report rather than introducing a separate workflow.

---

# Multi-Organization Data Isolation

Users can belong to multiple organizations through membership records.

Protected endpoints use the organization selected after login to determine the current membership.

Sensitive employee operations are therefore scoped through the current membership rather than only the user ID.

This design is particularly important for the right-to-delete requirement because deleting one organization's diagnostic must not delete another organization's data for the same user.

---

# Testing

The final test suite was run locally with:

```bash
cd backend
python -m pytest -q
```

Final result:

```text
23 passed
```

The suite covers behavior including:

- organization authorization
- cross-organization access prevention
- seniority-based question filtering
- small-group privacy
- department average calculation
- diagnostic validation
- duplicate question rejection
- employee deletion
- multi-organization deletion isolation
- AI response validation
- password hashing behavior
- legacy password migration
- personalized action-plan behavior

The test run also reports existing SQLAlchemy datetime deprecation warnings. They are warnings rather than test failures and were not part of the requested assessment scope.

---

# AI Usage

AI tools were used during development for implementation assistance, code review, debugging, and test design.

I did not treat AI-generated code as automatically correct. Changes were run against the repository's tests and corrected when the repository's actual behavior differed from an initial assumption.

One concrete example was the AI-scoring mock data. The inherited fixture contained malformed responses intended to exercise validation, but the same fixture pool was also used for normal runtime mock scoring. Manual testing exposed the mismatch because valid submissions could receive an intentionally invalid response. The runtime mock data was separated from invalid validation cases while retaining the strict scoring validation.

Another example was test setup for organization authorization: an initially proposed test assumed a seeded user belonged to an additional organization. The repository's seed data did not support that assumption, so the test was corrected using the actual organization data.

---

# Known Limitations / Technical Debt

- SQLite remains the default local database.
- Configuration uses a lightweight `.env` loader.
- The live AI integration depends on the configured OpenAI-compatible endpoint and model.
- The Personal AI Action Plan is intentionally deterministic and rule-based rather than dynamically generated by an LLM.
- The current test run emits SQLAlchemy datetime deprecation warnings that should be addressed in a future maintenance pass.

---

# Running Locally

## Backend

```bash
cd backend
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Or:

```bash
uvicorn app.main:app --reload
```

The seeded demo password is:

```text
pulse123
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://127.0.0.1:8000
```

## Tests

```bash
cd backend
python -m pytest -q
```

---

# Demo Accounts

All seeded users use the password `pulse123`.

| Email | Organization(s) | Role |
|---|---|---|
| asha@northwind.test | Northwind Logistics | Admin |
| meera@bluepeak.test | Bluepeak Retail | Admin |
| ravi@consult.test | Northwind Logistics + Bluepeak Retail | Employee at Northwind, Admin at Bluepeak |
| priya@northwind.test | Northwind Logistics | Employee, Support |
| dev@northwind.test | Northwind Logistics | Employee, Engineering Lead |

---

# AI Mode

## Mock

```text
AI_MODE=mock
```

This is the default local mode and uses the valid canned responses in:

```text
backend/data/mock_ai_responses.json
```

Malformed AI-output cases are tested separately by the scoring tests.

## Live

```text
AI_MODE=live
```

The application calls the configured OpenAI-compatible endpoint using:

```text
LLM_API_URL
LLM_API_KEY
LLM_MODEL
```

---

# Assessment Result

The two requested client changes have been implemented:

- small-group dashboard privacy
- employee right to delete diagnostic data

Additional authorization, validation, password-security, configuration, CORS, and AI-reliability issues were also hardened.

A new employee-facing Personal AI Action Plan feature was added.

Final local test result:

```text
23 passed
```