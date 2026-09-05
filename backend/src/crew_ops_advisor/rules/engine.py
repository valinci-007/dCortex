"""Compose the seven rules into a legality evaluation for one crew member.

`evaluate_duties` answers: "if this crew member operates these duty periods
(in addition to, or instead of, what they are already rostered for), is every
rule satisfied?" It returns a LegalityEvidence with one verdict per rule per
relevant day, so the answer is both checkable and explainable.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from crew_ops_advisor.domain.models import Certification, Crew, DutyClock, DutyPeriod, Ruleset
from crew_ops_advisor.rules import checks
from crew_ops_advisor.rules.verdicts import LegalityEvidence, RuleVerdict, VerdictStatus


@dataclass(frozen=True, slots=True)
class CrewContext:
    """Everything the rules need to know about one crew member."""

    crew: Crew
    clock: DutyClock
    certifications: tuple[Certification, ...]
    rostered_duties: tuple[DutyPeriod, ...]  # the whole schedule week, chronological

    @classmethod
    def load(cls, store, crew_id: str) -> CrewContext:  # store: crew_ops_advisor.data.Datastore
        return cls(
            crew=store.crew.get(crew_id),
            clock=store.duty_clocks.get(crew_id),
            certifications=tuple(store.certifications.for_crew(crew_id)),
            rostered_duties=tuple(store.pairings.duties_for_crew(crew_id)),
        )


def daily_totals(
    ctx: CrewContext, timeline: Iterable[DutyPeriod]
) -> tuple[dict[date, float], dict[date, float]]:
    """Duty and flight hours per calendar day: snapshot history plus the given timeline."""
    duty: dict[date, float] = defaultdict(float)
    flight: dict[date, float] = defaultdict(float)
    for h in ctx.clock.daily_history:
        duty[h.date] += h.duty_hours
        flight[h.date] += h.flight_hours
    for d in timeline:
        duty[d.date] += d.duty_hours
        flight[d.date] += d.flight_hours
    return dict(duty), dict(flight)


def evaluate_duties(
    ctx: CrewContext,
    ruleset: Ruleset,
    duties: Sequence[DutyPeriod],
    *,
    replacing: Iterable[str | tuple[str, date]] = (),
    callout: bool = False,
) -> LegalityEvidence:
    """Evaluate all seven rules for `duties` operated by `ctx.crew`.

    replacing: rostered duties to drop from the timeline first — a pairing id drops
        the whole pairing, a (pairing_id, date) pair drops one day of it (e.g. the
        crew's own duty when re-evaluating it after a delay).
    callout: the duties are a reserve/day-off callout, so RULE-BASE-07 applies.
    """
    proposed = sorted(duties, key=lambda d: d.report_utc)
    if not proposed:
        raise ValueError("evaluate_duties needs at least one duty period")
    dropped_pairings = {r for r in replacing if isinstance(r, str)}
    dropped_days = {r for r in replacing if not isinstance(r, str)}
    existing = [
        d
        for d in ctx.rostered_duties
        if d.pairing_id not in dropped_pairings and (d.pairing_id, d.date) not in dropped_days
    ]
    timeline = sorted(existing + proposed, key=lambda d: d.report_utc)
    proposed_ids = {id(d) for d in proposed}
    verdicts: list[RuleVerdict] = []

    # RULE-FDP-01 — each proposed duty period on its own
    verdicts.extend(checks.check_fdp(d, ruleset) for d in proposed)

    # RULE-DUTY-02 / RULE-FLT-03 — every duty day whose window is affected by the proposal
    duty_by_date, flight_by_date = daily_totals(ctx, timeline)
    first, last = proposed[0].date, proposed[-1].date
    duty_days = int(ruleset.param(checks.DUTY, "window_days"))
    flight_days = int(ruleset.param(checks.FLT, "window_days"))
    timeline_dates = sorted({d.date for d in timeline})
    for day in timeline_dates:
        if first <= day <= last + timedelta(days=duty_days - 1):
            verdicts.append(checks.check_duty_window(duty_by_date, day, ruleset))
        if first <= day <= last + timedelta(days=flight_days - 1):
            verdicts.append(checks.check_flight_window(flight_by_date, day, ruleset))

    # RULE-REST-04 — gaps around each proposed duty, plus the snapshot rest baseline
    rest: list[RuleVerdict] = []
    for prev, nxt in zip(timeline, timeline[1:], strict=False):
        prev_new, nxt_new = id(prev) in proposed_ids, id(nxt) in proposed_ids
        if prev_new or nxt_new:
            rest.append(
                checks.check_rest_gap(prev, nxt, ruleset, downstream=prev_new and not nxt_new)
            )
    # last_rest_ended is (latest release up to the snapshot) + 12h, and that latest duty may
    # itself be a rostered snapshot-day duty in the timeline — so the baseline only binds
    # duties that begin after the snapshot with nothing rostered before them.
    if timeline[0] is proposed[0] and proposed[0].report_utc > ctx.clock.as_of_utc:
        rest.append(checks.check_rest_baseline(proposed[0], ctx.clock.last_rest_ended, ruleset))
    verdicts.extend(
        rest or [RuleVerdict(checks.REST, VerdictStatus.PASS, "no adjacent duties to rest against")]
    )

    # RULE-QUAL-05 — once per aircraft type
    for actype in sorted({d.aircraft_type for d in proposed}):
        verdicts.append(checks.check_rating(ctx.crew, actype))

    # RULE-CERT-06 — once per proposed duty date
    for day in sorted({d.date for d in proposed}):
        verdicts.append(checks.check_certifications(ctx.certifications, day))

    # RULE-BASE-07 — where the first proposed duty starts
    verdicts.append(checks.check_base(ctx.crew, proposed[0].dep_station, callout=callout))

    return LegalityEvidence(
        crew_id=ctx.crew.crew_id,
        verdicts=tuple(verdicts),
        duty_dates=tuple(sorted({d.date for d in proposed})),
    )


def evaluate_rostered(
    ctx: CrewContext, ruleset: Ruleset, pairing_id: str, *, on: date | None = None
) -> LegalityEvidence:
    """Re-evaluate a crew member's own rostered pairing (optionally one day of it)."""
    own = [
        d
        for d in ctx.rostered_duties
        if d.pairing_id == pairing_id and (on is None or d.date == on)
    ]
    if not own:
        raise ValueError(
            f"{ctx.crew.crew_id} is not rostered on {pairing_id}" + (f" on {on}" if on else "")
        )
    return evaluate_duties(ctx, ruleset, own, replacing=[(d.pairing_id, d.date) for d in own])
