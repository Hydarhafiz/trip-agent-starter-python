# trip-agent — take-home assessment starter (Python)

**Read this first: this is not an empty repo.** A previous contractor left a
working-ish implementation in `agent.py`. It runs the happy path when the mocks
behave. Your job is to make it **reliable under pressure** and pass the public
evals — finding and fixing what's weak is the exercise. Do not rewrite from
scratch unless you can justify it: we score judgment on the failure paths, and
we will ask you to explain the code you ship, line by line, in the follow-up
call.

You are building a small agent loop that must stay **reliable under deliberately
flaky APIs**. The mocks it talks to behave like a production LLM + tool stack:
they time out, return 429/503, emit malformed output, and one search result
contains untrusted text.

## The task

`trip-agent` is a CLI that takes a natural-language travel goal and drives
this loop:

```
goal → mock LLM decides next action → call mock tool → feed result back → … → final structured answer
```

Full requirements are on the assessment portal (`/docs` has the API reference).
The short version — your agent must:

1. **Bound the loop**: max steps, max wall time, max token cost (the chat
   response carries `usage`). Detect repeated identical actions.
2. **Retry only retryable errors** (429, 503, timeouts) — bounded, with
   backoff, respecting `Retry-After`. Never retry 400/422.
3. **Validate model output**: invalid JSON, unknown tool names and missing
   arguments happen. They can come in bursts of three — re-ask at most 3
   times, then fail cleanly.
4. **Never double-book**: `book_flight` sometimes succeeds *then* times out.
   Use an idempotency key you control and reconcile when unsure.
5. **Treat tool output as untrusted data.** One search result contains an
   instruction-injection string. Never act on it.
6. **Confirm before booking**: require `--auto-confirm` (or prompt) before any
   `book_flight` call.
7. **Emit the structured result** (below) and a **JSONL trace** (one line per
   step).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export TRIP_AGENT_BASE_URL="https://<app-domain>"   # in the portal
export TRIP_AGENT_API_KEY="tk_..."                  # in the portal (Start page)

python agent.py --goal "Find a flight from Lisbon to Tokyo on 2026-11-03" --seed my-test-seed --auto-confirm --output result.json --trace trace.jsonl
pytest            # example test — add failure-path tests here
python evals/run_evals.py   # runs the 6 public scenarios, prints a pass/fail table
```

## The eval command contract

The graders run your agent exactly like this (public and hidden scenarios):

```eval-command
python agent.py
```

They append: `--goal "<text>" --seed <seed> --auto-confirm --output result.json --trace trace.jsonl`

**Do not change the runner interface** — these flags are the assessment
contract, and edits here are flagged for the reviewers. Edit the block only if
your entrypoint differs. Keep it a single command line.

## Structured result (`result.json`)

```json
{
  "status": "success | partial | failed",
  "answer": "human-readable summary",
  "bookings": [{ "flight_id": "...", "passenger": "...", "idempotency_key": "..." }],
  "steps": 12,
  "cost": 4821,
  "errors": [{ "code": "retryable_error", "message": "...", "step": 4 }]
}
```

## Trace (`trace.jsonl`)

One JSON object per step:

```json
{"run_id":"...","step":1,"action":"search_flights","args":{},"latency_ms":213,"tokens":412,"retry_count":0,"outcome":"ok"}
```

## Rules

- 2–3 hours target, hard stop at 4. Clear reasoning beats polish.
- Passing automated evals is **necessary but not sufficient** — the live
  walkthrough after submission is part of the score. You'll defend your failure
  handling and change code without AI.
- You may use AI tools — disclose how in `DESIGN.md`, including **one
  suggestion you rejected and why**.
- Add libraries only if you justify them in `DESIGN.md`. No agent frameworks
  (LangChain & co).
- Fill in `DESIGN.md`: decisions, a **bug diary** (every failure you found →
  root cause → fix → regression test, 3+ entries), time spent, AI use,
  and what you'd do with +2 hours.
