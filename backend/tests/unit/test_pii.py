"""PII minimisation (ADR-0017): names never leave the machine in minimal mode."""

from __future__ import annotations

import pytest

from crew_ops_advisor.agent.pii import WITHHELD, PiiGuard


@pytest.fixture(scope="module")
def guard(store):
    return PiiGuard(store, "minimal")


def test_full_mode_changes_nothing(store):
    g = PiiGuard(store, "full")
    payload = {"crew_id": "C-1042", "name": "A. Nair"}
    assert g.scrub_result(payload) == (payload, 0)
    assert g.scrub_text("A. Nair is sick") == ("A. Nair is sick", 0)
    assert not g.active


def test_names_are_dropped_from_crew_records_and_pseudonymised_in_text(guard):
    unique_id = next(i for i, n in guard.directory.items() if n in guard._id_for_name)
    unique_name = guard.directory[unique_id]
    payload = {
        "count": 2,
        "reserves": [
            {
                "crew_id": unique_id,
                "name": unique_name,
                "rank": "Captain",
                "reachability_minutes": 45,
            },
            {"crew_id": "C-9999", "crew_name": "Z. Nobody", "medical_expires": "2026-10-08"},
        ],
        "rule": {"name": "RULE-REST-04"},  # not a crew record: kept
        "message": f"Dear {unique_name}, please report at 05:30Z",
    }
    scrubbed, removed = guard.scrub_result(payload)
    names = str(scrubbed)
    assert unique_name not in names and "Z. Nobody" not in names
    assert scrubbed["reserves"][0] == {
        "crew_id": unique_id,
        "rank": "Captain",
        "reachability_minutes": 45,
    }
    assert scrubbed["reserves"][1] == {"crew_id": "C-9999", "medical_expires": "2026-10-08"}
    assert scrubbed["rule"] == {"name": "RULE-REST-04"}
    assert scrubbed["message"] == f"Dear {unique_id}, please report at 05:30Z"
    assert removed == 3


def test_ambiguous_names_are_withheld_not_guessed(guard):
    shared = next((n for n in guard.directory.values() if n not in guard._id_for_name), None)
    if shared is None:
        pytest.skip("dataset has no duplicated names")
    text, n = guard.scrub_text(f"{shared} called in sick")
    assert text == f"{WITHHELD} called in sick" and n == 1


def test_model_facing_registry_scrubs_but_the_raw_registry_does_not(store, registry, guard):
    wrapped = guard.wrap(registry)
    raw = registry.call("list_reserves", {"station": "BLR", "date": "2026-09-15"}).result
    sent = wrapped.call("list_reserves", {"station": "BLR", "date": "2026-09-15"}).result
    assert all("name" in r for r in raw["reserves"])
    assert not any("name" in r for r in sent["reserves"])
    assert [r["crew_id"] for r in raw["reserves"]] == [r["crew_id"] for r in sent["reserves"]]
    assert wrapped.names() == registry.names()
    assert wrapped.definitions() == registry.definitions()


def test_invalid_mode_is_rejected(store):
    with pytest.raises(ValueError, match="CREW_OPS_PII_MODE"):
        PiiGuard(store, "paranoid")
