# DESIGN.md — trip-agent

## Development time

The developer reports 150 minutes of cumulative active work before finalization,
including implementation, reviews and manual hosted evaluations. This replaces
older partial snapshots. Finalization is measured from 2026-10-30 01:36:43
Asia/Kuala_Lumpur. At 2026-10-30 01:45:46, finalization measures 9.1 minutes.
The recorded total is **159.1 minutes (2.65 hours)**: 150 developer-reported
minutes plus this measured phase, within the 240-minute cap. This checkpoint
includes documentation, offline verification and source-package preparation.
Pauses between earlier messages are excluded. Portal submission and the live
walkthrough have not happened and are not included.

## Architecture and execution flow

The starter architecture remains: `agent.py` owns the CLI, validation, orchestration,
retries, booking decisions, progress and evidence; `client.py` is a synchronous
httpx wrapper for the Jubilabs mock APIs. No framework, database, external LLM or
new dependency was introduced. Request/response dictionaries remain at the existing
JSON boundary rather than adding a second model layer.

1. `main()` parses the unchanged goal/seed/confirmation/output/trace flags and
   creates a run ID, trace and HTTP client. Credentials come from exported process
   variables; the CLI does not load dotenv files.
2. `run_agent()` sends the goal/history to the mock planner, validates one action,
   checks budgets and user intent, then uses a cached result or executes a tool.
3. Sanitized tool feedback contains the full response as JSON-string content with
   tool and result. Confirmed flights/weather/booking, not model prose, determine
   whether the requested work is complete.
4. `_finish()` builds the structured result. `main()` attempts result output,
   trace output and client close even if an earlier finalizer fails. Unexpected
   programming errors propagate instead of being disguised as API failures.

## Reliability and safety decisions

| Fault / boundary | Policy and tradeoff |
| --- | --- |
| HTTP 503 | At most two immediate retries with bounded backoff. A later read proposal can recover after one exhausted group; exhaustion is not permanent unavailability. Failures never enter the success cache. |
| HTTP 429 | Respect valid numeric or HTTP-date Retry-After values. Invalid values fall back to bounded exponential backoff. Stop if the required wait cannot fit the deadline. |
| Slow responses | Clamp call timeout to remaining time and reject late read/planner responses. The fixed monotonic deadline is never reset between cycles. |
| Hanging requests | Retry documented timeouts within bounds. Treat booking timeouts as uncertain writes and reconcile before considering a same-key retry. |
| Malformed planner output | Validate envelope, supported tool, JSON-string object arguments, required strings and dates. Re-ask at most three times; the fourth consecutive invalid response stops cleanly. |
| Repeated actions | Cache full sanitized reads by action plus canonical arguments. Count all occurrences per valid signature, including failed and cached ones, so alternating loops also stop. |
| Prompt injection | Sanitize the known instruction pattern and mark feedback untrusted. Execution-time intent, eligibility and passenger checks supply the booking safety boundary; text filtering is not a universal injection detector. |
| Stale weather | Refresh once per exact request, with bounded transport retries inside that refresh. Cache the resulting response. Persistent staleness or failed refresh is disclosed and prevents full success. |
| Other HTTP errors | Do not retry 400/403/422 or other statuses outside the documented retry allowlist. |

Local limits are 24 logical iterations, 90 seconds, 20,000 planner tokens and three
occurrences per identical valid action. Chat permits five retries; reads and
bookings permit two. Backoff starts at 0.4 seconds and caps at eight seconds,
except valid Retry-After waits. These values are local policies, not grader
thresholds. An identical search can make at most three groups of three HTTP
attempts before a fourth proposal stops without HTTP; earlier run limits win.
Weather has its separately bounded one-time refresh. Sustained outages can still
fail safely; allowing later recovery deliberately spends more bounded requests.

### Booking authorisation and constraints

Auto-confirm bypasses the operator prompt, not intent/eligibility checks. Recognized
booking prohibitions override positive booking words. Names must be one complete
supported clause: capitalized Unicode components, with internal hyphens/apostrophes;
initials, multiple people or unsupported prose fail before requests rather than
booking a truncated identity. The grammar is intentionally bounded.

Book only a flight from an eligible search. Check documented origin, destination,
date, price_eur and nonstop fields, explicit passenger, confirmation and booking
intent. Cheapest ties are allowed among eligible fares. Bare budgets mean EUR;
recognized explicit non-EUR markers are rejected without an invented conversion.
Under/below/less-than limits are strict; maximum/at-most limits are inclusive.

### Idempotency and reconciliation

Derive one key from the literal goal, flight and passenger; reuse it on every
attempt and across identical runs. A booking may commit before its response times
out. Reconcile with a bounded, seeded booking-list read and require exact key,
flight and passenger matches. Preserve the real key and record; never fabricate
one from a flight-only match. A 503 never commits under the official contract.

After an unprovable outcome, stop further booking and report uncertainty. A
non-timeout booking transport error triggers reconciliation but no automatic write
retry. Repeated completed proposals return the confirmed record; a different
additional booking is blocked. Cross-goal semantic deduplication is not implemented.

## Completion, result and trace

Success requires normal planner termination and all requested work: validated
search, fresh matching weather when requested, and confirmed booking when requested.
A completed empty search truthfully reports no options; an empty booking search
fails. Useful incomplete work normally produces partial. Fatal booking-goal failures
remain failed if no booking is confirmed. A confirmed booking survives later errors,
with partial status when remaining work or termination fails. Final summaries use
observed data, so planner prose cannot invent fulfilment.

One JSONL row represents one planner iteration, including retries and tool work.
Numbering starts at one before a planner attempt. Final answers, malformed output,
cache hits and handled failures retain a row. Pre-loop failures have zero steps and
an empty trace. Each row contains run_id, step, action, args, latency_ms, tokens,
retry_count and outcome. Latency includes the whole iteration and waits. Retry count
sums extra transport attempts actually started, including reconciliation retries;
a weather refresh is a semantic read, and a cache hit is neither a retry nor HTTP.

Tokens sum valid prompt_tokens plus completion_tokens from successful chat
responses, including malformed messages, finals and late responses. Result cost
equals summed trace tokens. The final response may cross a token limit whose cost
was unknown in advance: record actual usage and stop. Exact-limit finals are
allowed; no further planner request or tool side effect follows exhaustion. No
undocumented total_tokens field is assumed. Errors retain recovered and terminal
failures. Expected request/configuration failures produce structured artifacts.
An unwritable output path still raises its filesystem error after remaining
finalizers are attempted; output cannot be guaranteed to an unwritable location.

## Bug diary

Tests are in [tests/test_reliability.py](tests/test_reliability.py). Fixtures are
illustrative examples of the supplied official contract, not hosted captures.

| Observed failure | Root cause | Correction | Regression test |
| --- | --- | --- | --- |
| HTTP 400 caused another request | Classifier retried every status >=400 | Retry only 429/503/timeouts | test_fatal_http_errors_are_attempted_once |
| Commit-then-timeout caused another POST before reconciliation | Fresh key per attempt; lookup only after attempts | Reuse one key and reconcile exact identity immediately | test_timeout_after_commit_reconciles_exact_identity; test_booking_retries_reuse_one_key |
| Missing search arguments raised KeyError | Required fields indexed without validation | Validate before dispatch; bounded re-asking | test_fourth_malformed_output_stops_without_tool_calls |
| Do-not-book goal booked with auto-confirm | Positive keyword detection ignored negation | Prohibitions override booking intent | test_negated_booking_blocks_auto_confirm |
| Maria Silva Santos could be booked as Maria Silva | Two-word prefix accepted as identity | Preserve complete supported clause; reject ambiguity | test_truncated_passenger_is_rejected_before_correct_booking; test_ambiguous_passenger_fails_without_any_request |
| Requested weather was omitted but status was success | Completion ignored weather | Track actual requested work | test_missing_requested_work_cannot_report_success |
| Stale weather was not refreshed | Warning replaced required refresh | One refresh and honest remaining-staleness status | test_stale_weather_is_refetched_once_and_disclosed |
| Cached search returned another request's flights | Cache used latest global results | Cache complete responses by exact signature | test_read_cache_restores_the_matching_full_result |
| Trace count/fields disagreed with steps | Per-attempt logging mixed with post-chat numbering | One complete finally-recorded row per iteration | test_trace_has_one_complete_measured_row_per_iteration |
| Final-answer tokens bypassed budget | Cost check required a tool call | Charge before message handling; check finals too | test_final_answer_usage_is_charged_and_budgeted |
| Runtime API error skipped artifacts/cleanup | Finalizers followed only successful execution | Handle expected errors and always attempt finalization | test_main_finalizes_artifacts_and_closes_client; test_output_write_failure_still_closes_trace_and_client |
| Hosted 04 failed after three search 503s: failed, 3 steps, 534 tokens, no booking | failed_cycle_signatures made temporary exhaustion permanent | Remove permanent guard; allow later bounded read recovery; cache successes only | test_transient_read_exhaustion_recovers_on_later_iteration; test_persistent_read_failure_stops_at_action_limit; test_fatal_read_after_transient_exhaustion_is_not_retried |

## Verification and known limitations

- Final offline suite: **155/155 passed**. Commands: `python3 -B -m pytest -q -p no:cacheprovider` and `git diff --check`.
- The developer ran the unchanged hosted public evaluator and confirmed **6/6**.
  Scenarios 01–05 returned success; 06 returned expected failure. Booking scenarios
  passed the evaluator's server-side delta or verified-replay checks. Local result
  and trace artifacts have consistent step counts and token totals. Codex made no
  hosted requests and did not repeat the evaluations during finalization.
- Initial hosted run was 5/6; only 04 failed. Its retry-exhaustion defect was
  reproduced offline, corrected and passed on the developer's subsequent run.
- All eight fault categories have offline coverage. Hosted evidence demonstrates
  503/429 recovery, malformed-output recovery, repeated booking suppression and a
  search timeout. A hosted booking commit-before-timeout, injection encounter,
  stale-weather fault and isolated slow-response fault are not confirmed. This
  coverage distinction is not a claim that every failure path ran live.
- Six regression cases failed against the original starter (three root causes);
  13 authorization cases failed before correction; five D–E cases failed against
  Batch 1; eight read-recovery cases failed before their focused correction.
- MockTransport blocks real HTTP in tests; fake clocks verify budgets. CLI cleanup
  tests use a synthetic empty environment. No credentials are inspected.
- HTTPX timeouts are cooperative/per I/O phase, not an exact process kill.
  Interactive confirmation can wait for the operator; evals use auto-confirm.
- The parser is deliberately limited; no general natural-language interpreter or
  universal injection detector is claimed. The payload keeps the starter's chat
  interface: hosted public compatibility is demonstrated, while the supplied
  reference extract does not specify the tools-array descriptor schema.
- Missing usage follows the starter's zero convention; malformed usage is rejected
  and unavailable counts cannot be reconstructed. Cost is known token usage, not
  a claim about provider billing. Filesystem permissions and abrupt process kills
  can prevent artifact persistence.
- Generated outputs, Git metadata, caches, virtual environments, credentials and
  SDD handoffs are excluded from the source-only submission archive. The included
  .env.example is generated from known placeholders and is not copied from .env.
- Public/hidden evaluation flags, scenarios, evaluator and dependency list remain
  unchanged. Hidden evaluation results are unknown. The live walkthrough remains.

## AI tools used and rejected suggestion

Codex, through the ChatGPT conversation, assisted repository review, planning,
implementation, regression tests and acceptance audits. Follow-up AI-assisted
review exposed negation, passenger-truncation and evidence gaps; hosted failure
evidence drove the narrow read-recovery correction. The developer approved batches,
ran hosted evaluations and owns the final code and unassisted walkthrough.
No external LLM service was added to the application.

A separate trace/state abstraction was considered and rejected. This bounded CLI
needs explicit progress flags, dictionaries and one per-iteration trace record;
an additional layer would add navigation without improving the present contract.
The separate uncertain-booking path remains justified by its write/reconciliation
invariant. AI-assisted changes were checked against the supplied contract and
regression evidence; public evaluation success is not a substitute for ownership.

## What I would do with two more hours

1. Rehearse the commit-timeout, stale-weather, malformed-output and budget paths,
   then make a small manual change without AI in preparation for the walkthrough.
2. Add live fault evidence only if the assessment requires it; retain current
   passing public results rather than repeatedly running scenarios for polish.
3. Extend input grammar only for a demonstrated unsupported goal and clarify the
   full tools-array contract before changing the working HTTP interface.
