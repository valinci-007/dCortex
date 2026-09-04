from app.rules.result import RuleCheckResult
from app.rules.rule_config import get_rule


def calculate_remaining_flight_hours(flight_hours_28d: float) -> float:
    rule = get_rule("RULE-FLT-03")
    max_flight_hours = rule["params"]["max_flight_hours"]

    return max(0.0, max_flight_hours - flight_hours_28d)


def check_flight_hours(
    flight_hours_28d: float,
    additional_flight_hours: float = 0.0,
) -> RuleCheckResult:
    rule = get_rule("RULE-FLT-03")
    max_flight_hours = rule["params"]["max_flight_hours"]

    projected_hours = flight_hours_28d + additional_flight_hours
    passed = projected_hours <= max_flight_hours

    if passed:
        detail = (
            f"Projected flight {projected_hours:.2f}h is within "
            f"the {max_flight_hours:.2f}h limit."
        )
    else:
        excess = projected_hours - max_flight_hours
        detail = (
            f"Projected flight {projected_hours:.2f}h exceeds "
            f"the {max_flight_hours:.2f}h limit by {excess:.2f}h."
        )

    return RuleCheckResult(
        rule_id="RULE-FLT-03",
        passed=passed,
        detail=detail,
    )