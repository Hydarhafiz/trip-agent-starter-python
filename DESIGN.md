# DESIGN.md — trip-agent

Fill this in as you go. It is read before the debrief.

## How I spent my time

- (approximate, honest)

## Design decisions

- (decision → why → what I gave up)

## Failure taxonomy

How I classify errors and what the agent does for each class:
(e.g. retryable transport / fatal client error / malformed model output / untrusted content / budget exhaustion)

## AI tools I used, and how

- (disclose honestly; include ONE suggestion you rejected and why)

## Bug diary (required — at least 3 entries)

Batch 1 evidence only; final submission documentation remains in slice E.
The following regressions were run against an isolated copy of the original
starter and failed there; they pass against the Batch 1 implementation.

| Failure observed | Root cause | Fix | Regression in tests/test_reliability.py |
| --- | --- | --- | --- |
| HTTP 400 caused another request on chat, search, weather and booking | Retry classifier accepted every status >= 400 | Retry only 429/503/timeouts; fatal responses stop without retry or final sleep | test_fatal_http_errors_are_attempted_once |
| A simulated booking committed, timed out, then received another POST before reconciliation | Fresh key per attempt and reconciliation only after all booking attempts | One stable key; reconcile immediately after uncertain writes by exact key/flight/passenger; preserve real booking records | test_timeout_after_commit_reconciles_exact_identity; test_booking_retries_reuse_one_key |
| Missing search arguments raised KeyError instead of bounded recovery | Required fields were indexed without validation | Validate envelope, tool name, JSON object, required strings and date before dispatch; allow three re-asks | test_fourth_malformed_output_stops_without_tool_calls; test_three_malformed_outputs_recover_without_tool_side_effects |

Additional Batch 1 protections: fixed 90-second monotonic deadline and bounded
Retry-After waits; exact reconciliation with seed propagation; suppression of
completed repeated bookings; route/date/passenger eligibility and cheapest,
nonstop and EUR budget checks against the supplied official API fields.

Verification: Python 3.12.3, httpx 0.28.1, pytest 9.0.2 already installed.
Initial starter tests: 2 passed. Batch 1 suite: 104 passed (102 new parameterized
cases plus the existing 2) before the acceptance audit; 118 passed after the
C1/C2 corrections (14 additional cases). Six selected cases failed against the original
starter as expected. Tests use httpx.MockTransport, reject real HTTP, and fake
time/sleep. No hosted evaluation or server-side success is claimed.

The existing client, CLI flags, README command and evaluation files are unchanged.
The sanitized contract and local budget/validation policies are recorded in
docs/core/api-contract.md. No new dependency, framework, storage or service was
introduced. The natural-language parser remains deliberately limited.

The acceptance audit found two further booking-authorization defects. Thirteen
new cases failed against the prior Batch 1 implementation before this correction;
they now pass, plus one additional terminal-initial ambiguity case.

| Failure observed | Root cause | Fix | Regression in tests/test_reliability.py |
| --- | --- | --- | --- |
| An explicit do-not-book goal still issued a simulated booking with auto-confirm | Positive booking keyword detection ignored negation | Recognized prohibitions override booking intent, so proposals cannot reach booking dispatch | test_negated_booking_blocks_auto_confirm |
| Maria Silva Santos could be booked as Maria Silva | Passenger regex accepted a two-word prefix and validation trusted it | Validate the entire supported name clause; preserve every component; fail before requests when ambiguous | test_truncated_passenger_is_rejected_before_correct_booking; test_complete_supported_passenger_identity_is_preserved; test_ambiguous_passenger_fails_without_any_request |

The supported name grammar and conservative booking-prohibition policy are
documented in docs/core/api-contract.md. No hosted calls or Batch 2 work was done.

## What I'd do with +2 more hours

- (ranked, with reasons)

- (ranked, with reasons)
