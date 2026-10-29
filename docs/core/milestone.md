# Jubilabs agent reliability assessment

Status: complete; implementation and finalization approved. Offline verification
is 155/155 and the developer's unchanged hosted public evaluation is 6/6. Portal
submission and the unassisted live walkthrough remain manual developer actions.

## Scope and contracts

Preserve the Python CLI, synchronous HTTP client, dependencies, six public
scenarios and evaluation command. README.md owns the CLI/result/trace contracts;
DESIGN.md explains the current design, decisions, evidence, limitations and AI use.
The sanitized official API extract is recorded in api-contract.md.

| Slice | Completed outcome | Evidence |
| --- | --- | --- |
| A | Retry only temporary errors; bounded attempts and one run deadline | Transport, fatal-error, Retry-After and fake-clock regressions |
| B | Stable booking key and exact server reconciliation | Commit-timeout, identity-mismatch, unknown-outcome and replay regressions |
| C | Validated actions, authorisation, complete supported passenger identity and flight constraints | Malformed output, negation, identity, eligibility, price and confirmation regressions |
| D | Fact-based completion, exact cache, loop bounds, one weather refresh and sanitized feedback | Completion, cache, repetition, weather and injection regressions |
| E | Complete per-iteration trace, token/retry/latency accounting and handled-failure artifacts | Trace, budget, client/configuration and cleanup regressions |

Batch 1 checkpoint: 86e5c14852687cdd55376f225e715116fd73fb0b (118 offline cases).
The final feature retains the approved Batch 2 changes, its focused read-recovery
correction, final documentation and sanitized example in one completion commit.
No workflow-only or separate documentation-release commit is required.

## Completion evidence and retention

- 155 offline cases pass; git diff --check passes. All 118 Batch 1 cases remain.
- Hosted run initially passed 5/6; 04 exposed the permanent transient-read guard.
  Eight offline cases failed before its correction. The developer's subsequent
  unchanged public evaluation passed all six, including server booking checks.
- All eight fault categories have offline coverage. Live injection, stale weather,
  isolated slowness and booking commit-timeout coverage remains unconfirmed.
- Unique capability regressions and authoritative public scenarios are retained.
  There is one production path; no obsolete parallel implementation remains.
- The source ZIP contains an explicit source allowlist and a generated placeholder
  example. Credentials, Git metadata, caches, generated outputs, virtual
  environments and ephemeral SDD state are excluded. No remote push or submission
  is authorized by finalization.
