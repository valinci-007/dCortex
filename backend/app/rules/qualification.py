from app.rules.result import RuleCheckResult


def has_aircraft_rating(
    ratings: list,
    aircraft_type: str,
) -> bool:
    return aircraft_type in ratings


def check_aircraft_qualification(
    ratings: list,
    aircraft_type: str,
) -> RuleCheckResult:
    qualified = has_aircraft_rating(ratings, aircraft_type)

    if qualified:
        detail = (
            f"Crew holds a valid {aircraft_type} aircraft rating."
        )
    else:
        detail = (
            f"Crew does not hold a valid {aircraft_type} "
            f"aircraft rating."
        )

    return RuleCheckResult(
        rule_id="RULE-QUAL-05",
        passed=qualified,
        detail=detail,
    )