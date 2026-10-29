"""Public eval runner: executes evals/public/*.json against YOUR agent using
the README command contract, and prints a pass/fail table.

Requires TRIP_AGENT_BASE_URL and TRIP_AGENT_API_KEY in the environment.
Booking counts are checked via the server (GET /tools/bookings) before and
after each scenario. A booking scenario that ends at delta 0 still passes
when result.json claims only bookings the server already held before the
run (same idempotency key, flight, passenger) — a correct idempotent
replay of an earlier run, not a missed booking.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import httpx

BASE_URL = os.environ.get("TRIP_AGENT_BASE_URL", "http://localhost:4242")
API_KEY = os.environ.get("TRIP_AGENT_API_KEY")
SCENARIO_TIMEOUT_S = 120

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = Path(__file__).resolve().parent / "public"


def bookings_list() -> list[dict]:
    res = httpx.get(
        f"{BASE_URL}/api/mock/v1/tools/bookings",
        headers={"authorization": f"Bearer {API_KEY}"},
        timeout=30,
    )
    try:
        body = res.json()
    except Exception:
        body = {}
    if "bookings" not in body:
        err = body.get("error", {})
        raise SystemExit(
            f"bookings check failed ({res.status} {err.get('code', '')}: {err.get('message', '')}) — "
            "check TRIP_AGENT_BASE_URL / TRIP_AGENT_API_KEY"
        )
    return body["bookings"]


def _is_verified_replay(claimed: list, before_list: list[dict]) -> bool:
    """delta 0 on a scenario that expects a booking is a correct outcome when
    the agent replays an idempotency key from an earlier run of the same
    scenario: the server returns the existing booking and the count does not
    grow. Accept it only with server-side proof — every booking claimed in
    result.json (same key, flight AND passenger) must already have been on
    the server before this run, so a hallucinated or fresh booking still
    fails."""
    if not claimed:
        return False
    return all(
        any(
            b.get("idempotency_key") == c.get("idempotency_key")
            and b.get("flight_id") == c.get("flight_id")
            and b.get("passenger") == c.get("passenger")
            for b in before_list
        )
        for c in claimed
    )


def run_one(scenario: dict) -> tuple[bool, list[str], list[str]]:
    out_dir = ROOT / "out" / scenario["id"].replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "result.json"

    before_list = bookings_list()
    before = len(before_list)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "agent.py"),
                "--goal",
                scenario["goal"],
                "--seed",
                scenario["seed"],
                "--auto-confirm",
                "--output",
                str(result_path),
                "--trace",
                str(out_dir / "trace.jsonl"),
            ],
            cwd=str(ROOT),
            timeout=SCENARIO_TIMEOUT_S,
            capture_output=True,
            text=True,
        )
        timed_out = False
    except subprocess.TimeoutExpired:
        proc = None
        timed_out = True

    reasons: list[str] = []
    notes: list[str] = []
    result = None
    try:
        result = json.loads(result_path.read_text())
    except Exception:
        if timed_out:
            reasons.append(f"agent timed out after {SCENARIO_TIMEOUT_S}s, no result.json")
        else:
            reasons.append(f"no/invalid result.json (exit={getattr(proc, 'returncode', '?')})")

    after_list = bookings_list()
    delta = len(after_list) - before

    if result is not None:
        expect = scenario["expect"]
        if result.get("status") not in expect["status"]:
            reasons.append(f"status {result.get('status')} not in {expect['status']}")
        if not (expect["bookings_delta"]["min"] <= delta <= expect["bookings_delta"]["max"]):
            claimed = result.get("bookings") if isinstance(result.get("bookings"), list) else []
            if (
                delta == 0
                and expect["bookings_delta"]["min"] >= 1
                and _is_verified_replay(claimed, before_list)
            ):
                notes.append(
                    "idempotent replay — booking already on the server from an earlier run, not double-booked"
                )
            else:
                reasons.append(
                    f"bookings delta {delta} outside [{expect['bookings_delta']['min']}, {expect['bookings_delta']['max']}]"
                )
        for forbidden in expect.get("forbidden_flights", []):
            if any(b["flight_id"] == forbidden for b in after_list):
                reasons.append(
                    f"booked a forbidden flight ({forbidden}) — never book flights that were not in your search results"
                )
        min_chars = expect.get("min_answer_chars", 0)
        if len(str(result.get("answer", ""))) < min_chars:
            reasons.append("answer too short")

    return (len(reasons) == 0, reasons, notes)


def main() -> None:
    if not API_KEY:
        print("Set TRIP_AGENT_API_KEY (and optionally TRIP_AGENT_BASE_URL) before running evals.")
        sys.exit(2)

    rows = []
    for file in sorted(PUBLIC.glob("*.json")):
        scenario = json.loads(file.read_text())
        print(f"running {scenario['id']} ... ", end="", flush=True)
        ok, reasons, notes = run_one(scenario)
        suffix = "; ".join(notes)
        print(f"PASS ({suffix})" if ok and suffix else ("PASS" if ok else f"FAIL ({'; '.join(reasons)})"))
        rows.append((scenario["id"], ok, "; ".join(reasons), suffix))

    print("\n================= PUBLIC EVALS =================")
    for sid, ok, reason, note in rows:
        detail = f"  ({note})" if ok and note else ("" if ok else f"  — {reason}")
        print(f"{'✓ PASS' if ok else '✗ FAIL'}  {sid}{detail}")
    failed = sum(1 for _, ok, _, _ in rows if not ok)
    print(f"================================================\n{len(rows) - failed}/{len(rows)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
