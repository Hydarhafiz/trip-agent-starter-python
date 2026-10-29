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

For each bug you found and fixed: failure observed → root cause → the fix →
where the regression test lives. Example row:

- `book_flight retried with a fresh key` → timeout-after-commit turned the retry into a second booking → derive one stable key before the loop and retry with it → `tests/booking_idempotency.test.ts`

- (entry 2)

- (entry 3)

## What I'd do with +2 more hours

- (ranked, with reasons)

- (ranked, with reasons)
