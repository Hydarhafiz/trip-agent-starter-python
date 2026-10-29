# Jubilabs agent reliability assessment

Status: Batch 1 (A–C) approved after 118 passing offline tests.
No hosted calls authorized. Batch 2 has not started.

## Sources and boundaries

- README.md defines retries, confirmation, malformed-output recovery, budgets,
  result/trace contracts, submission documentation and the unchanged CLI.
- client.py and evals/run_evals.py establish existing request fields and booking
  identity (idempotency_key, flight_id, passenger). Public scenarios stay unchanged.
- The user supplied the sanitized official API reference during Batch 1; the
  relevant contract and remaining tool-declaration ambiguity are recorded in
  [api-contract.md](api-contract.md). Flight eligibility uses documented
  flight_id, origin, destination, date, price_eur and nonstop fields.
- Preserve existing working paths; replace defective retry/reconciliation logic
  directly. No parallel implementation or migration compatibility is needed.
- Local tests only. No credentials, dependency installs, hosted calls or public
  eval runs. Keep changes reviewable at the Batch 1 checkpoint.

## Batch 1: transport, booking and action validation

Type: build. Route: builder-executor -> tdd-loop.
Status: complete and approved; 118 offline tests and git diff --check pass.
Contained correction route: fix-bug -> tdd-loop (C1 negation, C2 full identity).

- A: retry only 429, 503 and timeouts; honor Retry-After within one monotonic
  deadline; bound attempts, calls and sleeps; never retry fatal HTTP responses.
- B: reuse one stable booking key; reconcile uncertain writes by exact key,
  flight and passenger; seed and bound reconciliation; suppress completed
  duplicate bookings; stop unresolved booking sequences.
- C: validate envelopes and one tool call, JSON arguments, required nonempty
  strings and dates; allow three malformed re-asks; enforce explicit route,
  date, passenger and booking intent; reject flights outside verified results.
  Enforce cheapest/nonstop/budget only using the official flight schema.
- Acceptance: offline regression tests prove bounded request counts, stable
  keys and matching server evidence, no unauthorized side effects, clean
  malformed-output handling and preserved CLI flags.
- Evidence: pytest with fake clocks, scripted clients and httpx.MockTransport;
  git diff --check. No formatter/linter/type configuration exists; do not add it.
- Completion boundary: one focused feature commit when the complete admitted
  feature is verified and commit authorization is established. No workflow-only
  commits. Stop after offline Batch 1 verification for user review.
- Evidence: baseline 2 tests passed; current suite 118 passed (116 new cases).
  Six selected regressions failed against an isolated original-starter copy as
  expected. No hosted tests run. The client, CLI, README and eval files are intact.
- C1/C2 evidence: 13 new cases reproduced failures in the prior Batch 1 code;
  all now pass, along with an additional terminal-initial ambiguity case.
  Explicit prohibition prevents auto-confirm booking. Complete supported names
  are preserved; truncated proposals are rejected; ambiguous names fail before
  any request. No general natural-language parser was introduced.
- Implementation choices: 90-second fixed deadline, unchanged stable key hash,
  three booking attempts, exact reconciliation, ties allowed for cheapest,
  unsupported non-EUR budget rejected. No generic workflow layer or new package.
- Remaining ambiguity: the supplied chat request example includes tools but does
  not define tool-declaration descriptors or whether they are mandatory. Preserve
  the existing client payload until further official evidence warrants a change.

## Batch 2: completion and evidence (not started)

Type: build. Route: builder-executor -> tdd-loop. Requires Batch 1 review.

- D: correct action cache, bounded repetition, required-work completion and
  accurate weather freshness disclosure, using official freshness requirements.
- E: complete per-step tracing, accounting and handled-failure artifacts;
  finish DESIGN.md, bug diary, time record, AI disclosure and explainability.
- Acceptance: focused offline tests, then separately authorized unchanged public
  evaluation command; server/result booking reconciliation; final diff review.

## Retention and explainability

Keep unique capability regressions in tests/. Keep this milestone compact and
decisions in DESIGN.md; generated outputs and handoff remain ignored. No extra
evidence registry, quality toolchain, release artifacts or framework is needed.
Track actual verification and limitations; never imply hosted success from mocks.
