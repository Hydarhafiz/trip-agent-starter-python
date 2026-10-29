# Assessment API contract used for Batch 1

Authority: sanitized official Jubilabs Mock API Reference supplied by the user
from the assessment portal during Batch 1. Fixtures in tests/ are illustrative
examples of this contract, not captured hosted responses.

- POST `/api/mock/v1/tools/search_flights`: request `origin`, `dest`, `date`.
  Response `results` contains `flight_id`, `origin`, `destination`, `date`,
  `price_eur` (EUR), `nonstop` (boolean), and descriptive fields such as airline,
  depart, duration_minutes and optional untrusted notes. Same-city searches can
  legitimately return an empty array. Only flights from an eligible search may
  be booked.
- POST `/api/mock/v1/llm/chat`: messages, seed and a tools array in the documented
  request example. Response message contains tool_calls (tool name and
  JSON-string arguments) or final content, plus token usage. Preserve the existing
  client's request shape: the provided extract does not specify tool-declaration
  descriptor shapes or whether the tools array is mandatory. No tool declaration
  schema is invented. Existing agent usage fields are prompt_tokens and
  completion_tokens; no undocumented total_tokens field is assumed.
- Tool messages contain JSON-string content with `tool` and `result`, where
  result is the full response object. Preserve booking record metadata rather
  than fabricating a smaller booking response.
- POST `/api/mock/v1/tools/book_flight`: request `flight_id`, `passenger`,
  `idempotency_key`. Response `booking` has booking_id, flight_id, passenger,
  idempotency_key and booked_at; optional idempotent_replay. Same key replays the
  existing booking; a different key can duplicate it. A booking can commit before
  a roughly 12-second response hang. A 503 never commits a booking.
- GET `/api/mock/v1/tools/bookings`: `bookings` array of booking records. Match
  key, flight and passenger for reconciliation.
- POST `/api/mock/v1/tools/get_weather`: request city and YYYY-MM-DD date;
  response city, date, temperature_c, conditions, stale. Refetch stale weather
  once and report remaining staleness (Batch 2, slice D).
- Retry 429 with Retry-After, 503 with bounded backoff, and timeouts. 400, 403
  and 422 are non-retryable. Seeds belong in chat body and tool query parameters.

Local policy: validate one tool call at a time and three consecutive re-asks;
allow ties for cheapest eligible fare. Bare numeric budgets use the API's EUR
currency; explicit non-EUR budgets are rejected rather than silently converted.
`under/below/less than` are strict; `maximum/at most` are inclusive. The existing
limited natural-language parser remains; this is not a general travel interpreter.

Booking prohibitions (do not/don't/never/must not/not to book or reserve,
optionally automatically, and no bookings/reservations) override positive booking
keywords. Conflicting instructions therefore fail safely for booking.
Passenger identity must be one complete `for` or `passenger [name]` clause,
optionally followed by a recognized trailing budget. Supported names contain
capitalized Unicode letter components longer than one character, with internal
hyphens or apostrophes allowed. Preserve all components exactly. Initials,
multiple people, lowercase components or additional unrecognized prose are
ambiguous and cause booking goals to fail before any API request.
