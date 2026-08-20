# tests/test_tools.py

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
from app.tools.ndvi_tool import ndvi_tool


def make_test_analysis_result():
    return AnalysisResult(
        analysis_type="ndvi_analysis",
        findings={
            "mean_ndvi": 0.5,
            "minimum_ndvi": 0.1,
            "maximum_ndvi": 0.8,
            "ndvi_std_dev": 0.15,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        data_quality=DataQuality(
            source_image_count=100,
            usable_image_count=50,
            valid_coverage=1.0,
        ),
        methodology=Methodology(
            dataset="COPERNICUS/S2_SR_HARMONIZED",
            resolution_m=10,
            composite_method="median",
            cloud_masking="QA60",
            index="NDVI = (B8 - B4) / (B8 + B4)",
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


@patch("app.tools.ndvi_tool.validate_analysis_result")
@patch("app.tools.ndvi_tool.analyze_ndvi")
def test_ndvi_tool(
    mock_analyze,
    mock_validate,
):
    expected_result = make_test_analysis_result()
    expected_validation = make_test_validation_result()

    mock_analyze.return_value = expected_result
    mock_validate.return_value = expected_validation

    aoi = "test-aoi"

    result, validation = ndvi_tool(
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
        max_cloud_percentage=20.0,
        scale=10,
    )

    mock_validate.assert_called_once_with(expected_result)