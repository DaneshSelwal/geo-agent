from app.models.analysis import AnalysisResult
from app.models.validation import (
    ValidationCheck,
    ValidationResult,
)


def validate_analysis_result(
    result: AnalysisResult,
) -> ValidationResult:
    """
    Validate an AnalysisResult before it is passed
    to the agent/reporting layer.

    Generic validation checks are applied to every
    analysis, while analysis-specific checks are
    handled separately.
    """

    checks: list[ValidationCheck] = []

    # --------------------------------------------------
    # Generic Check 1: Source imagery
    # --------------------------------------------------

    source_count = result.data_quality.source_image_count

    checks.append(
        ValidationCheck(
            name="source_images_available",
            passed=source_count > 0,
            message=(
                f"{source_count} source images found."
                if source_count > 0
                else "No source images were found."
            ),
        )
    )

    # --------------------------------------------------
    # Generic Check 2: Usable imagery
    # --------------------------------------------------

    usable_count = result.data_quality.usable_image_count

    checks.append(
        ValidationCheck(
            name="usable_images_available",
            passed=usable_count > 0,
            message=(
                f"{usable_count} usable images found."
                if usable_count > 0
                else "No usable images remain after filtering."
            ),
        )
    )

    # --------------------------------------------------
    # Generic Check 3: Minimum number of observations
    # --------------------------------------------------

    minimum_images = 5

    enough_images = usable_count >= minimum_images

    checks.append(
        ValidationCheck(
            name="sufficient_image_count",
            passed=enough_images,
            message=(
                f"Usable image count ({usable_count}) is sufficient."
                if enough_images
                else (
                    f"Only {usable_count} usable images found. "
                    f"At least {minimum_images} are recommended."
                )
            ),
        )
    )

    # --------------------------------------------------
    # Generic Check 4: Spatial coverage
    # --------------------------------------------------

    coverage = result.data_quality.valid_coverage

    minimum_coverage = 0.70

    sufficient_coverage = coverage >= minimum_coverage

    checks.append(
        ValidationCheck(
            name="sufficient_spatial_coverage",
            passed=sufficient_coverage,
            message=(
                f"Valid coverage is {coverage:.1%}."
                if sufficient_coverage
                else (
                    f"Valid coverage is only {coverage:.1%}. "
                    f"At least {minimum_coverage:.0%} is recommended."
                )
            ),
        )
    )

    # --------------------------------------------------
    # Analysis-specific checks
    # --------------------------------------------------

    if result.analysis_type == "ndvi_analysis":
        checks.append(_validate_ndvi_range(result))

    elif result.analysis_type == "landcover_analysis":
        checks.append(_validate_landcover_distribution(result))

    # --------------------------------------------------
    # Calculate quality score
    # --------------------------------------------------

    passed_checks = sum(check.passed for check in checks)

    total_checks = len(checks)

    quality_score = passed_checks / total_checks if total_checks > 0 else 0.0

    # --------------------------------------------------
    # Determine quality level
    # --------------------------------------------------

    quality_level = _get_quality_level(
        quality_score,
        checks,
    )

    # --------------------------------------------------
    # Collect issues
    # --------------------------------------------------

    issues = [check.message for check in checks if not check.passed]

    # --------------------------------------------------
    # Overall validity
    # --------------------------------------------------

    valid = all(check.passed for check in checks)

    return ValidationResult(
        valid=valid,
        quality_score=quality_score,
        quality_level=quality_level,
        checks=checks,
        issues=issues,
    )


def _validate_landcover_distribution(
    result: AnalysisResult,
) -> ValidationCheck:
    """
    Validate the Dynamic World land-cover distribution.

    The distribution should:
        - exist
        - contain at least one class
        - contain proportions between 0 and 1
        - sum approximately to 1
    """

    distribution = result.findings.get("landcover_distribution")

    if not distribution:
        return ValidationCheck(
            name="landcover_distribution_valid",
            passed=False,
            message=("Land-cover distribution is missing " "or empty."),
        )

    values = list(distribution.values())

    values_valid = all(0.0 <= value <= 1.0 for value in values)

    if not values_valid:
        return ValidationCheck(
            name="landcover_distribution_valid",
            passed=False,
            message=(
                "One or more land-cover proportions " "are outside the [0, 1] range."
            ),
        )

    total = sum(values)

    distribution_valid = abs(total - 1.0) <= 0.01

    if not distribution_valid:
        return ValidationCheck(
            name="landcover_distribution_valid",
            passed=False,
            message=(
                f"Land-cover proportions sum to "
                f"{total:.4f}, expected approximately 1.0."
            ),
        )

    return ValidationCheck(
        name="landcover_distribution_valid",
        passed=True,
        message=(f"Land-cover distribution is valid " f"(sum={total:.4f})."),
    )


def _validate_ndvi_range(
    result: AnalysisResult,
) -> ValidationCheck:
    """
    Validate that the mean NDVI is within the
    expected NDVI range.
    """

    mean_ndvi = result.findings.get("mean_ndvi")

    ndvi_range_valid = mean_ndvi is not None and -1.0 <= mean_ndvi <= 1.0

    if mean_ndvi is None:
        message = "Mean NDVI is missing from the " "analysis findings."
    elif ndvi_range_valid:
        message = f"Mean NDVI = {mean_ndvi:.4f}."
    else:
        message = "Mean NDVI is outside the expected " "[-1, 1] range."

    return ValidationCheck(
        name="ndvi_range",
        passed=ndvi_range_valid,
        message=message,
    )


def _get_quality_level(
    quality_score: float,
    checks: list[ValidationCheck],
) -> str:
    """
    Determine qualitative analysis quality.

    Critical validation failures prevent an analysis
    from being classified as High quality.
    """

    critical_checks = {
        "sufficient_image_count",
        "sufficient_spatial_coverage",
    }

    critical_failure = any(
        check.name in critical_checks and not check.passed for check in checks
    )

    if critical_failure:
        if quality_score >= 0.60:
            return "Moderate"

        return "Low"

    if quality_score >= 0.80:
        return "High"

    if quality_score >= 0.60:
        return "Moderate"

    return "Low"
