from datetime import date, datetime

from app.rules.base import check_reserve_base
from app.rules.certification import check_certifications
from app.rules.duty import check_duty_hours
from app.rules.flight_hours import check_flight_hours
from app.rules.fdp import check_fdp
from app.rules.qualification import check_aircraft_qualification
from app.rules.rest import check_rest
from app.rules.result import LegalityResult, RuleCheckResult


def check_legality(
    *,
    fdp_hours: float,
    sector_count: int,
    duty_hours_7d: float,
    additional_duty_hours: float,
    flight_hours_28d: float,
    additional_flight_hours: float,
    previous_release: datetime | None,
    next_report: datetime | None,
    ratings: list,
    aircraft_type: str,
    certifications: list,
    duty_date: date,
    reserve_base: str | None = None,
    assignment_base: str | None = None,
) -> LegalityResult:
    checks: list[RuleCheckResult] = []

    checks.append(
        check_fdp(
            fdp_hours=fdp_hours,
            sector_count=sector_count,
        )
    )

    checks.append(
        check_duty_hours(
            duty_hours_7d=duty_hours_7d,
            additional_duty_hours=additional_duty_hours,
        )
    )

    checks.append(
        check_flight_hours(
            flight_hours_28d=flight_hours_28d,
            additional_flight_hours=additional_flight_hours,
        )
    )

    if previous_release is not None and next_report is not None:
        checks.append(
            check_rest(
                previous_release=previous_release,
                next_report=next_report,
            )
        )

    checks.append(
        check_aircraft_qualification(
            ratings=ratings,
            aircraft_type=aircraft_type,
        )
    )

    checks.append(
        check_certifications(
            certifications=certifications,
            duty_date=duty_date,
        )
    )

    if reserve_base is not None and assignment_base is not None:
        checks.append(
            check_reserve_base(
                reserve_base=reserve_base,
                assignment_base=assignment_base,
            )
        )

    return LegalityResult(
        legal=all(check.passed for check in checks),
        checks=checks,
    )