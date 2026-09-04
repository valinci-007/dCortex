"""The eval grader must be strict about numbers and lenient only where the data warrants."""

from crew_ops_advisor.evals import atoms, grade


def test_atoms_flatten_leaves_and_reduce_flight_ids_to_numbers():
    expected = {
        "duty_hours_7d": 20.93,
        "flights": ["DX412-2026-09-15", "DX413-2026-09-15"],
        "window": {"start": "06:00", "end": "18:00"},
        "count": 21,
        "legal": False,
    }
    assert atoms(expected) == ["20.93", "DX412", "DX413", "06:00", "18:00", "21", "false"]


def test_numbers_must_match_as_whole_numbers():
    assert grade("headroom 39.07h", 39.07).passed
    assert grade("headroom 139.07h", 39.07).passed is False
    assert grade("39.075", 39.07).passed is False
    assert grade("21 flights", 21).passed
    assert grade("2026-09-21", 21).passed is False
    assert grade("21.0 flights", 21).passed
    assert grade("23.50h block", 23.5).passed


def test_strings_are_case_insensitive_and_score_is_fractional():
    g = grade(
        "the captain is c-2210 at del", {"base": "DEL", "crew": "C-2210", "role": "First Officer"}
    )
    assert not g.passed and g.score == 0.667 and g.missing == ("First Officer",)


def test_empty_expected_passes():
    assert grade("anything", {}).passed


def test_rank_abbreviations_and_phrase_content_words_count():
    assert grade("C-3311 — FO A320", "First Officer").passed
    assert grade("C-2111 — SCC", "Senior Cabin Crew").passed
    assert grade("C-1329 — CC", "Cabin Crew").passed
    assert grade(
        "Short-rest pattern over the last 14 days", "short-rest pattern over last 14 days"
    ).passed
    assert grade(
        "two fatigue reports last month", "two fatigue reports this month"
    ).passed  # stopwords
    assert not grade(
        "long-rest pattern over last 14 days", "short-rest pattern over last 14 days"
    ).passed
    assert not grade("nothing here", "First Officer").passed


def test_structured_key_strings_are_graded_by_their_facts():
    key = "RULE-DUTY-02: would exceed 60h/7d by 1h20m on 2026-09-15 (total 61.33h)"
    assert grade(
        "Breaches RULE-DUTY-02 on 2026-09-15: 61.33h in the 7-day window, over the 60h limit by 1h20m",
        key,
    ).passed
    assert grade(
        "Breaches RULE-DUTY-02 on 15 Sep: 61.33h in 7 days vs 60h, over by 1h20m", key
    ).passed  # textual date
    assert not grade(
        "Breaches RULE-DUTY-02 on 15 Sep: 61.33h vs 60h, over by 1h20m", key
    ).passed  # window length missing
    assert not grade(
        "Breaches RULE-DUTY-02 on 2026-09-15: 61.08h, over by 1h05m", key
    ).passed  # wrong numbers
    rest = "RULE-REST-04: only 10.75h rest before P-2204 on 2026-09-17 (downstream conflict)"
    assert grade(
        "RULE-REST-04 downstream: release 16 Sep 14:45Z then report 17 Sep 01:30Z for P-2204 = 10.75h rest",
        rest,
    ).passed
    assert not grade("RULE-REST-04: 10.75h rest before P-2204", rest).passed  # date missing


def test_thousands_separators_and_currency_are_normalised():
    assert grade("costs ₹250,000 in direct cancellation cost", 250000).passed
    assert grade("18,500 INR", 18500).passed


def test_action_strings_rule_aliases_and_ranks():
    assert grade(
        "1. C-3310 — reserve callout, ₹18,500", "Assign Captain C-3310 (reserve callout)"
    ).passed
    assert grade("C-1526 (day off callout)", "Assign Captain C-1526 (day-off callout)").passed
    assert not grade("C-1526 (reserve callout)", "Assign Captain C-1526 (day-off callout)").passed
    assert grade(
        "passes RULE-FDP-01, DUTY-02, FLT-03", ["RULE-FDP-01", "RULE-DUTY-02", "RULE-FLT-03"]
    ).passed
    assert atoms({"rank": 3, "cost_inr": 24000}) == ["24000"]
    long = "delay exceeds crew FDP — re-crew tail legs from reserves or cancel"
    assert grade(
        "the delay exceeds the crew's FDP so tail legs must be re-crewed from reserves or cancelled",
        long,
    ).passed
