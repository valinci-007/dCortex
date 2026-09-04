from datetime import date

from app.rules.result import RuleCheckResult


def is_certification_valid(
    valid_from: date,
    valid_to: date,
    duty_date: date,
) -> bool:
    return valid_from <= duty_date <= valid_to


def check_certifications(
    certifications: list,
    duty_date: date,
) -> RuleCheckResult:
    invalid_certifications = [
        certification
        for certification in certifications
        if not is_certification_valid(
            certification.valid_from,
            certification.valid_to,
            duty_date,
        )
    ]

    if not invalid_certifications:
        return RuleCheckResult(
            rule_id="RULE-CERT-06",
            passed=True,
            detail=f"All certifications are valid on {duty_date.isoformat()}.",
        )

    invalid_types = ", ".join(
        certification.cert_type
        for certification in invalid_certifications
    )

    return RuleCheckResult(
        rule_id="RULE-CERT-06",
        passed=False,
        detail=(
            f"Invalid certification(s) on {duty_date.isoformat()}: "
            f"{invalid_types}."
        ),
    )