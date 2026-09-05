-- Normalised relational schema for the Crew Ops Advisor dataset.
-- data/*.json is the source of truth; this database is a derived artifact.
-- Datetimes are ISO-8601 UTC text ('...Z'); dates are 'YYYY-MM-DD' text.

PRAGMA foreign_keys = ON;

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE crew (
    crew_id              TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    rank                 TEXT NOT NULL,
    base                 TEXT NOT NULL,
    seniority            INTEGER NOT NULL,
    reachability_minutes INTEGER NOT NULL,
    status               TEXT NOT NULL
);
CREATE INDEX idx_crew_base_rank ON crew(base, rank);

CREATE TABLE crew_ratings (
    crew_id TEXT NOT NULL REFERENCES crew(crew_id),
    rating  TEXT NOT NULL,
    PRIMARY KEY (crew_id, rating)
);

CREATE TABLE flights (
    flight_id     TEXT PRIMARY KEY,
    flight_no     TEXT NOT NULL,
    date          TEXT NOT NULL,
    dep_station   TEXT NOT NULL,
    arr_station   TEXT NOT NULL,
    dep_utc       TEXT NOT NULL,
    arr_utc       TEXT NOT NULL,
    block_hours   REAL NOT NULL,
    aircraft      TEXT NOT NULL,
    aircraft_type TEXT NOT NULL,
    seats         INTEGER NOT NULL
);
CREATE INDEX idx_flights_date ON flights(date);
CREATE INDEX idx_flights_dep ON flights(dep_station, date);
CREATE INDEX idx_flights_aircraft ON flights(aircraft, dep_utc);

CREATE TABLE pairings (
    pairing_id TEXT PRIMARY KEY,
    aircraft   TEXT NOT NULL
);

CREATE TABLE pairing_days (
    pairing_id  TEXT NOT NULL REFERENCES pairings(pairing_id),
    date        TEXT NOT NULL,
    report_utc  TEXT NOT NULL,
    release_utc TEXT NOT NULL,
    PRIMARY KEY (pairing_id, date)
);

CREATE TABLE pairing_day_flights (
    pairing_id TEXT NOT NULL,
    date       TEXT NOT NULL,
    position   INTEGER NOT NULL,
    flight_id  TEXT NOT NULL REFERENCES flights(flight_id),
    PRIMARY KEY (pairing_id, date, position),
    FOREIGN KEY (pairing_id, date) REFERENCES pairing_days(pairing_id, date)
);
CREATE INDEX idx_pdf_flight ON pairing_day_flights(flight_id);

CREATE TABLE pairing_crew (
    pairing_id TEXT NOT NULL REFERENCES pairings(pairing_id),
    crew_id    TEXT NOT NULL REFERENCES crew(crew_id),
    role       TEXT NOT NULL,
    PRIMARY KEY (pairing_id, crew_id)
);
CREATE INDEX idx_pairing_crew_crew ON pairing_crew(crew_id);

CREATE TABLE flagged_exceptions (
    crew_id TEXT NOT NULL REFERENCES crew(crew_id),
    date    TEXT NOT NULL,
    rule    TEXT NOT NULL,
    note    TEXT NOT NULL,
    PRIMARY KEY (crew_id, date, rule)
);

CREATE TABLE duty_clocks (
    crew_id          TEXT PRIMARY KEY REFERENCES crew(crew_id),
    as_of_utc        TEXT NOT NULL,
    duty_hours_7d    REAL NOT NULL,
    flight_hours_28d REAL NOT NULL,
    last_rest_ended  TEXT NOT NULL
);

CREATE TABLE duty_daily (
    crew_id      TEXT NOT NULL REFERENCES crew(crew_id),
    date         TEXT NOT NULL,
    duty_hours   REAL NOT NULL,
    flight_hours REAL NOT NULL,
    PRIMARY KEY (crew_id, date)
);

CREATE TABLE reserves (
    crew_id      TEXT PRIMARY KEY REFERENCES crew(crew_id),
    base         TEXT NOT NULL,
    oncall_start TEXT NOT NULL,
    oncall_end   TEXT NOT NULL,
    note         TEXT NOT NULL DEFAULT ''
);

CREATE TABLE reserve_dates (
    crew_id TEXT NOT NULL REFERENCES reserves(crew_id),
    date    TEXT NOT NULL,
    PRIMARY KEY (crew_id, date)
);

CREATE TABLE certifications (
    crew_id    TEXT NOT NULL REFERENCES crew(crew_id),
    cert_type  TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to   TEXT NOT NULL,
    PRIMARY KEY (crew_id, cert_type)
);
CREATE INDEX idx_cert_valid_to ON certifications(valid_to);

CREATE TABLE risk_signals (
    crew_id               TEXT PRIMARY KEY REFERENCES crew(crew_id),
    as_of_utc             TEXT NOT NULL,
    disruption_risk_score REAL NOT NULL
);

CREATE TABLE risk_drivers (
    crew_id  TEXT NOT NULL REFERENCES risk_signals(crew_id),
    position INTEGER NOT NULL,
    driver   TEXT NOT NULL,
    PRIMARY KEY (crew_id, position)
);

CREATE TABLE costs (
    key   TEXT PRIMARY KEY,
    value REAL NOT NULL
);
