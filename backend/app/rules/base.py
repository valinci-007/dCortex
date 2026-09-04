from app.rules.result import RuleCheckResult


def check_reserve_base(
    reserve_base: str,
    assignment_base: str,
) -> RuleCheckResult:
    same_base = reserve_base == assignment_base

    if same_base:
        detail = (
            f"Reserve crew is based at {reserve_base}, "
            f"matching the assignment base."
        )
    else:
        detail = (
            f"Reserve crew is based at {reserve_base}, "
            f"while the assignment base is {assignment_base}. "
            f"Deadhead positioning is required."
        )

    return RuleCheckResult(
        rule_id="RULE-BASE-07",
        passed=same_base,
        detail=detail,
    )