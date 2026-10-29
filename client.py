"""Thin HTTP client for the mock APIs.

Typed request/response envelopes ONLY — deliberately NO retries, NO
validation, NO default timeout (httpx's is disabled here). That reliability
work is the assessment; write it in your agent (agent.py).
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class ApiEnvelope:
    def __init__(self, status: int, headers: httpx.Headers, body: Any):
        self.status = status
        self.headers = headers
        self.body = body

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class MockApiClient:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
            timeout=None,  # deliberately unset — timeouts are YOUR job
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, body: Any = None, timeout: float | None = None, seed: str | int | None = None) -> ApiEnvelope:
        params = {"seed": seed} if seed is not None else None
        res = self._client.request(
            method, path, content=json.dumps(body) if body is not None else None, timeout=timeout, params=params
        )
        try:
            parsed = res.json()
        except Exception:
            parsed = {"error": {"code": "bad_json", "message": "response was not JSON"}}
        return ApiEnvelope(res.status_code, res.headers, parsed)

    def chat(self, messages: list[dict], seed: str | int | None = None, timeout: float | None = None) -> ApiEnvelope:
        payload: dict[str, Any] = {"messages": messages}
        if seed is not None:
            payload["seed"] = seed
        return self._request("POST", "/api/mock/v1/llm/chat", payload, timeout)

    def search_flights(self, origin: str, dest: str, date: str, timeout: float | None = None, seed: str | int | None = None) -> ApiEnvelope:
        return self._request("POST", "/api/mock/v1/tools/search_flights", {"origin": origin, "dest": dest, "date": date}, timeout, seed)

    def get_weather(self, city: str, date: str, timeout: float | None = None, seed: str | int | None = None) -> ApiEnvelope:
        return self._request("POST", "/api/mock/v1/tools/get_weather", {"city": city, "date": date}, timeout, seed)

    def book_flight(self, flight_id: str, passenger: str, idempotency_key: str, timeout: float | None = None, seed: str | int | None = None) -> ApiEnvelope:
        return self._request(
            "POST",
            "/api/mock/v1/tools/book_flight",
            {"flight_id": flight_id, "passenger": passenger, "idempotency_key": idempotency_key},
            timeout,
            seed,
        )

    def list_bookings(self, timeout: float | None = None, seed: str | int | None = None) -> ApiEnvelope:
        return self._request("GET", "/api/mock/v1/tools/bookings", timeout=timeout, seed=seed)
