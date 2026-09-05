"""Entity extraction resolves ids, stations, dates, ranks and routes against the dataset."""

from datetime import date

import pytest

from crew_ops_advisor.agent.entities import EntityExtractor


@pytest.fixture(scope="module")
def ex(store):
    return EntityExtractor(store)


def test_ids_are_found_and_upper_cased(ex):
    e = ex.extract("can c-2087 cover p-2291 on dx412 (vt-dxc)? see rule-duty-02")
    assert e.crew_ids == ("C-2087",) and e.pairing_ids == ("P-2291",)
    assert (
        e.flight_nos == ("DX412",) and e.aircraft == ("VT-DXC",) and e.rule_ids == ("RULE-DUTY-02",)
    )


def test_dates_iso_textual_and_relative(ex):
    assert ex.extract("on 2026-09-15").dates == (date(2026, 9, 15),)
    assert ex.extract("on 15 Sep").dates == (date(2026, 9, 15),)
    assert ex.extract("on Sep 17, 2026").dates == (date(2026, 9, 17),)
    assert ex.extract("tomorrow").dates == (date(2026, 9, 15),)
    assert ex.extract("today").dates == (date(2026, 9, 14),)
    assert ex.extract("on Friday").dates == (date(2026, 9, 18),)
    assert ex.extract("no date here").dates == ()


def test_stations_from_codes_and_city_names_and_delay_is_not_del(ex):
    e = ex.extract("flights from Bangalore to Mumbai, delayed")
    assert e.stations == ("BLR", "BOM") and (e.dep_station, e.arr_station) == ("BLR", "BOM")
    assert "DEL" not in ex.extract("the delayed flight").stations


def test_routes_read_departure_first(ex):
    assert (ex.extract("BLR→BOM").dep_station, ex.extract("BLR→BOM").arr_station) == ("BLR", "BOM")
    e = ex.extract("flights arriving into BLR from DEL")
    assert (e.dep_station, e.arr_station) == ("DEL", "BLR")
    e = ex.extract("flights to HYD")
    assert (e.dep_station, e.arr_station) == (None, "HYD")
    e = ex.extract("flights depart DEL")
    assert (e.dep_station, e.arr_station) == ("DEL", None)


def test_ranks_windows_and_within_days(ex):
    assert ex.extract("how many captains at DEL").ranks == ("Captain",)
    assert ex.extract("the senior cabin crew on VT-DXB").ranks == ("Senior Cabin Crew",)
    assert ex.extract("all cabin crew").ranks == ("Cabin Crew",)
    assert ex.extract("expiring within 30 days").within_days == 30
    assert ex.extract("BLR closed 08:00–14:00Z").time_window == ("08:00", "14:00")
    assert "afternoon" in ex.extract("flights this afternoon").flags
