"""The offline router plans the right tool call for each question family, and refuses the rest."""

import pytest

from crew_ops_advisor.agent.offline_provider import OfflineRouter


@pytest.fixture(scope="module")
def router(store):
    return OfflineRouter(store)


@pytest.mark.parametrize(
    ("prompt", "tool", "args"),
    [
        (
            "Who is on reserve at BLR on 2026-09-15?",
            "list_reserves",
            {"station": "BLR", "date": "2026-09-15"},
        ),
        (
            "Who's on reserve at BLR tomorrow?",
            "list_reserves",
            {"station": "BLR", "date": "2026-09-15"},
        ),
        (
            "How many duty hours does C-1042 have left this week?",
            "get_duty_clock",
            {"crew_id": "C-1042"},
        ),
        (
            "Which flights depart DEL this afternoon?",
            "list_flights",
            {
                "date": "2026-09-14",
                "dep_station": "DEL",
                "dep_from_utc": "2026-09-14T12:00:00Z",
                "dep_to_utc": "2026-09-14T18:00:00Z",
            },
        ),
        (
            "Which flights depart DEL on 2026-09-15?",
            "list_flights",
            {"date": "2026-09-15", "dep_station": "DEL"},
        ),
        (
            "List crew whose licence expires in the next 30 days.",
            "list_expiring_certifications",
            {"from_date": "2026-09-15", "within_days": 30},
        ),
        (
            "Which aircraft operates DX412 on 2026-09-15?",
            "get_flight",
            {"flight_no": "DX412", "date": "2026-09-15"},
        ),
        ("What is C-2210's base and rating?", "get_crew", {"crew_id": "C-2210"}),
        ("Which crew are assigned to pairing P-2291?", "get_pairing", {"pairing_id": "P-2291"}),
        ("How many captains are based at DEL?", "list_crew", {"rank": "Captain", "base": "DEL"}),
        ("What is the longest block time in the schedule?", "schedule_stats", {}),
        (
            "Which stations does the network serve nonstop from BLR?",
            "list_routes",
            {"dep_station": "BLR"},
        ),
        (
            "Who is the Senior Cabin Crew on VT-DXB's pairing on 2026-09-16?",
            "find_pairings",
            {"aircraft": "VT-DXB", "date": "2026-09-16"},
        ),
        ("What is the disruption-risk score for C-1042?", "get_risk_signal", {"crew_id": "C-1042"}),
        ("What does RULE-FDP-01 say?", "get_rules", {}),
        ("What are the callout cost rates?", "get_costs", {}),
    ],
)
def test_routes_to_expected_tool(router, prompt, tool, args):
    plan = router.route(prompt)
    assert plan is not None, prompt
    names = [c.name for c in plan.calls]
    assert tool in names
    call = next(c for c in plan.calls if c.name == tool)
    assert call.arguments == args


@pytest.mark.parametrize(
    "prompt",
    [
        "Will fog delay BLR tomorrow?",
        "Book a hotel for C-1042",
        "What's the meaning of life?",
    ],
)
def test_out_of_scope_and_simulation_questions_are_not_routed(router, prompt):
    assert router.route(prompt) is None
    assert router.refusal(prompt).startswith("I can't answer that reliably")


@pytest.mark.parametrize(
    ("prompt", "tool", "args"),
    [
        (
            "Captain C-1042 just called in sick for tomorrow — which flights are now uncrewed?",
            "simulate_crew_removal",
            {"crew_id": "C-1042", "from_date": "2026-09-15"},
        ),
        (
            "Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291. Which flights are immediately uncrewed?",
            "simulate_crew_removal",
            {"crew_id": "C-1042", "pairing_id": "P-2291", "reported_utc": "2026-09-15T05:00:00Z"},
        ),
        (
            "If I move FO C-2087 onto DX412, does anyone breach a duty limit?",
            "check_assignment_legality",
            {"crew_id": "C-2087", "pairing_id": "P-2291"},
        ),
        (
            "If Captain C-2087 is assigned to cover P-2291 from 15 Sep, does any rule breach?",
            "check_assignment_legality",
            {"crew_id": "C-2087", "pairing_id": "P-2291", "from_date": "2026-09-15"},
        ),
        (
            "Station BLR is closed 14:00–20:00 — what's the crew impact?",
            "station_closure_impact",
            {"station": "BLR", "date": "2026-09-14", "start": "14:00", "end": "20:00"},
        ),
        (
            "VT-DXA is delayed 90 minutes before DX401 on 16 Sep. Does the rostered crew breach any limit?",
            "simulate_delay",
            {"date": "2026-09-16", "delay_hours": 1.5, "aircraft": "VT-DXA"},
        ),
        (
            "If DX404 on 16 Sep is cancelled, how many passengers are affected?",
            "cancellation_impact",
            {"flight_no": "DX404", "date": "2026-09-16"},
        ),
        (
            "A crew is released at 15:30Z on 16 Sep. What is the earliest they may report next?",
            "earliest_next_report",
            {"release_utc": "2026-09-16T15:30:00Z"},
        ),
        (
            "Which crew have 45 or more duty hours in the 7 days ending 2026-09-15?",
            "crew_near_limits",
            {"date": "2026-09-15", "min_duty_hours": 45.0},
        ),
        (
            "Can C-5417 legally operate their rostered VT-DXB duty on 19 Sep?",
            "check_rostered_legality",
            {"crew_id": "C-5417", "date": "2026-09-19"},
        ),
        (
            "The VT-DXE captain is sick on 16 Sep (called 01:30Z). Which reserve captains' on-call windows cover the callout?",
            "reserve_coverage",
            {
                "required_report_utc": "2026-09-16T03:00:00Z",
                "aircraft_type": "ATR72",
                "station": "BLR",
                "rank": "Captain",
            },
        ),
    ],
)
def test_tier2_questions_route_to_simulation_tools(router, prompt, tool, args):
    plan = router.route(prompt)
    assert plan is not None, prompt
    call = next(c for c in plan.calls if c.name == tool)
    assert call.arguments == args


@pytest.mark.parametrize(
    ("prompt", "tool", "expect"),
    [
        (
            "Captain C-1042 is out for pairing P-2291 (15–16 Sep). Produce ranked resolution options with costs and reasoning.",
            "recommend_cover",
            {"crew_id": "C-1042", "pairing_id": "P-2291", "from_date": "2026-09-15"},
        ),
        ("Captain C-1042 is out — what should I do?", "recommend_cover", {"crew_id": "C-1042"}),
        (
            "C-5417's recurrent training lapsed. Resolve their 19 Sep assignment.",
            "recommend_cover",
            {"crew_id": "C-5417", "from_date": "2026-09-19"},
        ),
        (
            "What is the cheapest legal way to cover the VT-DXF First Officer on 20 Sep if they call sick at 03:30Z?",
            "recommend_cover",
            {"crew_id": "C-4520", "reported_utc": "2026-09-20T03:30:00Z"},
        ),
        (
            "Both A320 captains (VT-DXA and VT-DXB) are sick at 00:30Z on 18 Sep. Give the optimal joint crewing plan.",
            "joint_cover_plan",
            None,
        ),
        (
            "After the 90-minute delay to VT-DXA on 16 Sep, what should Crew Control do about the FDP breach?",
            "resolve_delay_options",
            {"date": "2026-09-16", "delay_hours": 1.5, "aircraft": "VT-DXA"},
        ),
        (
            "Draft the callout notification to C-3310 for covering P-2291.",
            "draft_callout_notification",
            {"crew_id": "C-3310", "pairing_id": "P-2291"},
        ),
        (
            "If the desk wants a standing morning briefing, which three data points per aircraft line should it surface and why?",
            "morning_briefing",
            {"date": "2026-09-15"},
        ),
        (
            "BLR closes 08:00–14:00Z on 17 Sep. Outline the recovery plan across affected pairings.",
            "station_closure_impact",
            {"station": "BLR", "date": "2026-09-17", "start": "08:00", "end": "14:00"},
        ),
    ],
)
def test_tier3_questions_route_to_recommendation_tools(router, prompt, tool, expect):
    plan = router.route(prompt)
    assert plan is not None, prompt
    call = next(c for c in plan.calls if c.name == tool)
    if expect is not None:
        assert call.arguments == expect
    else:
        assert len(call.arguments["events"]) == 2
