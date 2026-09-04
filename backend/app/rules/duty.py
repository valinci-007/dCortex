from app.rules.result import RuleCheckResult
from app.rules.rule_config import get_rule


def calculate_remaining_duty_hours(duty_hours_7d: float) -> float:
    rule = get_rule("RULE-DUTY-02")
    max_duty_hours = rule["params"]["max_duty_hours"]

    return max(0.0, max_duty_hours - duty_hours_7d)


def check_duty_hours(
    duty_hours_7d: float,
    additional_duty_hours: float = 0.0,
) -> RuleCheckResult:
    rule = get_rule("RULE-DUTY-02")
    max_duty_hours = rule["params"]["max_duty_hours"]

    projected_hours = duty_hours_7d + additional_duty_hours
    passed = projected_hours <= max_duty_hours

    if passed:
        detail = (
            f"Projected duty {projected_hours:.2f}h is within "
            f"the {max_duty_hours:.2f}h limit."
        )
    else:
        excess = projected_hours - max_duty_hours
        detail = (
            f"Projected duty {projected_hours:.2f}h exceeds "
            f"the {max_duty_hours:.2f}h limit by {excess:.2f}h."
        )

    return RuleCheckResult(
        rule_id="RULE-DUTY-02",
        passed=passed,
        detail=detail,
    )