from unittest.mock import patch

from app.models.analysis import (
    AnalysisResult,
    DataQuality,
    Methodology,
)
from app.models.validation import (
    ValidationCheck,
    ValidationResult,
)
from app.tools.landcover_tool import landcover_tool


def make_test_analysis_result():
    return AnalysisResult(
        analysis_type="landcover_analysis",
        findings={
            "landcover_distribution": {
                "water": 0.10,
                "trees": 0.20,
                "grass": 0.10,
                "flooded_vegetation": 0.05,
                "crops": 0.20,
                "shrub_and_scrub": 0.05,
                "built": 0.20,
                "bare": 0.05,
                "snow_and_ice": 0.05,
            },
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        data_quality=DataQuality(
            source_image_count=100,
            usable_image_count=100,
            valid_coverage=1.0,
        ),
        methodology=Methodology(
            dataset="GOOGLE/DYNAMICWORLD/V1",
            resolution_m=10,
            composite_method="mode",
            cloud_masking=(
                "No additional cloud masking applied; "
                "Dynamic World observations used as provided"
            ),
            index="Dynamic World land-cover label",
        ),
        limitations=[],
        visualizations={},
    )


def make_test_validation_result():
    return ValidationResult(
        valid=True,
        quality_score=1.0,
        quality_level="High",
        checks=[
            ValidationCheck(
                name="test_check",
                passed=True,
                message="All good.",
            )
        ],
        issues=[],
    )


@patch("app.tools.landcover_tool.validate_analysis_result")
@patch("app.tools.landcover_tool.analyze_landcover")
def test_landcover_tool(
    mock_analyze,
    mock_validate,
):
    expected_result = make_test_analysis_result()
    expected_validation = make_test_validation_result()

    mock_analyze.return_value = expected_result
    mock_validate.return_value = expected_validation

    aoi = "test-aoi"

    result, validation = landcover_tool(
        aoi=aoi,
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    assert result == expected_result
    assert validation == expected_validation

    mock_analyze.assert_called_once_with(
        aoi="test-aoi",
        start_date="2025-01-01",
        end_date="2025-12-31",
        scale=10,
    )

    mock_validate.assert_called_once_with(expected_result)