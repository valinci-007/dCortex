from datetime import datetime

from app.rules.result import RuleCheckResult
from app.rules.rule_config import get_rule


def calculate_rest_hours(
    previous_release: datetime,
    next_report: datetime,
) -> float:
    return (next_report - previous_release).total_seconds() / 3600


def check_rest(
    previous_release: datetime,
    next_report: datetime,
) -> RuleCheckResult:
    rule = get_rule("RULE-REST-04")
    min_rest_hours = rule["params"]["min_rest_hours"]

    rest_hours = calculate_rest_hours(
        previous_release,
        next_report,
    )

    passed = rest_hours >= min_rest_hours

    if passed:
        detail = (
            f"Rest {rest_hours:.2f}h meets the "
            f"{min_rest_hours:.2f}h minimum."
        )
    else:
        shortage = min_rest_hours - rest_hours
        detail = (
            f"Rest {rest_hours:.2f}h is below the "
            f"{min_rest_hours:.2f}h minimum by {shortage:.2f}h."
        )

    return RuleCheckResult(
        rule_id="RULE-REST-04",
        passed=passed,
        detail=detail,
    )