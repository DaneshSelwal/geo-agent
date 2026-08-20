from pydantic import BaseModel, Field


class ValidationCheck(BaseModel):
    """
    Result of a single validation check.
    """

    name: str
    passed: bool
    message: str


class ValidationResult(BaseModel):
    """
    Overall validation result for an analysis.
    """

    valid: bool

    quality_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    quality_level: str

    checks: list[ValidationCheck] = Field(default_factory=list)

    issues: list[str] = Field(default_factory=list)
