from app.rules.result import RuleCheckResult
from app.rules.rule_config import get_rule


def calculate_max_fdp(sector_count: int) -> float:
    rule = get_rule("RULE-FDP-01")
    params = rule["params"]

    extra_sectors = max(0, sector_count - params["free_sectors"])

    return (
        params["base_fdp_hours"]
        - extra_sectors * params["reduction_per_extra_sector_hours"]
    )


def check_fdp(
    fdp_hours: float,
    sector_count: int,
) -> RuleCheckResult:
    max_fdp = calculate_max_fdp(sector_count)

    passed = fdp_hours <= max_fdp

    return RuleCheckResult(
        rule_id="RULE-FDP-01",
        passed=passed,
        detail=(
            f"FDP {fdp_hours:.2f}h is within the "
            f"{max_fdp:.2f}h limit for {sector_count} sectors."
            if passed
            else
            f"FDP {fdp_hours:.2f}h exceeds the "
            f"{max_fdp:.2f}h limit for {sector_count} sectors."
        ),
    )