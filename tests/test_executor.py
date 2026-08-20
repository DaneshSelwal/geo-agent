# tests/test_executor.py
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
import app.agent.executor as executor


def make_test_result():
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
            index="NDVI",
        ),
        limitations=[],
        visualizations={},
    )


def make_test_validation():
    return ValidationResult(
        valid=True,
        quality_score=1.0,
        quality_level="High",
        checks=[
            ValidationCheck(
                name="test",
                passed=True,
                message="Passed",
            )
        ],
        issues=[],
    )


def test_execute_ndvi_tool(monkeypatch):

    expected_result = make_test_result()
    expected_validation = make_test_validation()

    def fake_ndvi_tool(**kwargs):
        return expected_result, expected_validation

    monkeypatch.setitem(
        executor.TOOLS,
        "ndvi_analysis",
        fake_ndvi_tool,
    )

    arguments = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [76.80, 28.35],
                    [77.20, 28.35],
                    [77.20, 28.65],
                    [76.80, 28.65],
                    [76.80, 28.35],
                ]
            ],
        },
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }

    with patch("app.agent.executor.geojson_to_ee_geometry") as mock_converter:

        mock_converter.return_value = "fake-ee-geometry"

        result, validation = executor.execute_tool(
            "ndvi_analysis",
            arguments,
        )

    assert result == expected_result
    assert validation == expected_validation

    mock_converter.assert_called_once_with(arguments["aoi"])


def test_unknown_tool():
    from app.agent.executor import execute_tool

    try:
        execute_tool(
            "does_not_exist",
            {},
        )
        assert False
    except ValueError as exc:
        assert "Unknown tool" in str(exc)


def test_invalid_scale():
    from app.agent.executor import execute_tool

    arguments = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [],
        },
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "scale": -10,
    }

    try:
        execute_tool(
            "ndvi_analysis",
            arguments,
        )
        assert False
    except Exception:
        pass
