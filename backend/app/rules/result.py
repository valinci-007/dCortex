from pydantic import BaseModel, Field


class RuleCheckResult(BaseModel):
    rule_id: str
    passed: bool
    detail: str


class LegalityResult(BaseModel):
    legal: bool
    checks: list[RuleCheckResult] = Field(default_factory=list)