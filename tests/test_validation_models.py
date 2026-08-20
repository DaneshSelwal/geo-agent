import pytest
from pydantic import ValidationError

from app.models.validation import (
    ValidationCheck,
    ValidationResult,
)


def test_validation_check_creation():
    check = ValidationCheck(
        name="test_check",
        passed=True,
        message="Check passed.",
    )

    assert check.name == "test_check"
    assert check.passed is True
    assert check.message == "Check passed."


def test_validation_result_creation():
    result = ValidationResult(
        valid=True,
        quality_score=1.0,
        quality_level="High",
    )

    assert result.valid is True
    assert result.quality_score == 1.0
    assert result.quality_level == "High"
    assert result.checks == []
    assert result.issues == []


@pytest.mark.parametrize(
    "score",
    [-0.1, 1.1, 2.0],
)
def test_quality_score_must_be_between_zero_and_one(score):
    with pytest.raises(ValidationError):
        ValidationResult(
            valid=True,
            quality_score=score,
            quality_level="High",
        )