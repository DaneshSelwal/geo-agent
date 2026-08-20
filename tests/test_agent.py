from unittest.mock import patch

from app.agent.agent import run_agent
from app.models.analysis import (
    AnalysisResult,
    DataQuality,
    Methodology,
)
from app.models.validation import (
    ValidationCheck,
    ValidationResult,
)
from tests.test_landcover_tool import (
    make_test_analysis_result,
    make_test_validation_result,
)


def make_invalid_analysis_result():
    return AnalysisResult(
        analysis_type="ndvi_analysis",
        findings={
            "mean_ndvi": 0.3,
            "minimum_ndvi": -0.2,
            "maximum_ndvi": 0.8,
            "ndvi_std_dev": 0.2,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
        },
        data_quality=DataQuality(
            source_image_count=10,
            usable_image_count=3,
            valid_coverage=0.4,
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


def make_invalid_validation_result():
    return ValidationResult(
        valid=False,
        quality_score=0.4,
        quality_level="Low",
        checks=[
            ValidationCheck(
                name="sufficient_image_count",
                passed=False,
                message="Usable image count is insufficient.",
            ),
        ],
        issues=[
            "Insufficient usable images.",
        ],
    )


def test_agent_stops_when_replan_also_fails():

    invalid_result = make_invalid_analysis_result()
    invalid_validation = make_invalid_validation_result()

    initial_function_call = type(
        "FunctionCall",
        (),
        {
            "name": "ndvi_analysis",
            "args": {
                "aoi": {},
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        },
    )()

    replan_function_call = type(
        "FunctionCall",
        (),
        {
            "name": "ndvi_analysis",
            "args": {
                "aoi": {},
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        },
    )()

    initial_response = object()
    replan_response = object()

    with patch(
        "app.agent.agent.ask_gemini",
        return_value=initial_response,
    ), patch(
        "app.agent.agent.extract_function_call",
        return_value=initial_function_call,
    ), patch(
        "app.agent.agent.execute_function_call",
        side_effect=[
            (
                invalid_result,
                invalid_validation,
            ),
            (
                invalid_result,
                invalid_validation,
            ),
        ],
    ) as mock_execute, patch(
        "app.agent.agent.generate_replan_response",
        return_value=replan_response,
    ), patch(
        "app.agent.agent.get_tool_call_from_response",
        return_value=replan_function_call,
    ), patch(
        "app.agent.agent.generate_final_response",
    ) as mock_final:

        result = run_agent("Analyze vegetation.")

    assert result["status"] == "validation_failed"

    assert mock_execute.call_count == 2

    mock_final.assert_not_called()


def test_agent_executes_replan_after_invalid_analysis():

    invalid_result = make_invalid_analysis_result()
    invalid_validation = make_invalid_validation_result()

    valid_result = make_test_analysis_result()
    valid_validation = make_test_validation_result()

    initial_function_call = type(
        "FunctionCall",
        (),
        {
            "name": "ndvi_analysis",
            "args": {
                "aoi": {},
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        },
    )()

    replan_function_call = type(
        "FunctionCall",
        (),
        {
            "name": "ndvi_analysis",
            "args": {
                "aoi": {},
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        },
    )()

    initial_response = object()
    replan_response = object()

    with patch(
        "app.agent.agent.ask_gemini",
        return_value=initial_response,
    ), patch(
        "app.agent.agent.extract_function_call",
        side_effect=[
            initial_function_call,
        ],
    ), patch(
        "app.agent.agent.execute_function_call",
        side_effect=[
            (
                invalid_result,
                invalid_validation,
            ),
            (
                valid_result,
                valid_validation,
            ),
        ],
    ) as mock_execute, patch(
        "app.agent.agent.generate_replan_response",
        return_value=replan_response,
    ), patch(
        "app.agent.agent.get_tool_call_from_response",
        return_value=replan_function_call,
    ), patch(
        "app.agent.agent.generate_final_response",
        return_value="Final answer",
    ) as mock_final:

        result = run_agent("Analyze vegetation.")

    assert result == "Final answer"

    assert mock_execute.call_count == 2

    mock_final.assert_called_once()
