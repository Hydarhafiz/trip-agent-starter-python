"""Example tests — replace/augment with your own failure-path tests."""

from agent import parse_args, validate_result


def test_parses_eval_contract_arguments():
    args = parse_args(
        ["--goal", "Find a flight", "--seed", "7", "--auto-confirm", "--output", "r.json", "--trace", "t.jsonl"]
    )
    assert args.goal == "Find a flight"
    assert args.seed == "7"
    assert args.auto_confirm is True


def test_rejects_structurally_invalid_result():
    assert len(validate_result({"status": "nope"})) > 0
    assert (
        validate_result(
            {"status": "success", "answer": "x", "bookings": [], "steps": 1, "cost": 2, "errors": []}
        )
        == []
    )
