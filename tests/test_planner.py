# tests/test_planner.py

from unittest.mock import patch

from app.agent.gemini import create_analysis_plan, synthesize_analysis_results
from app.models.plan import (
    AnalysisPlan,
    AnalysisStep,
)

from app.agent.planner import execute_plan
from app.agent.planner import run_planned_analysis
from app.agent.planner import plan_and_execute
from tests.test_landcover_tool import (
    make_test_analysis_result,
    make_test_validation_result,
)
from tests.test_tool import (
    make_test_analysis_result as make_test_analysis_result_ndvi,
    make_test_validation_result,
)


def test_create_analysis_plan():

    expected_plan = AnalysisPlan(
        objective=("Assess urbanization impact on vegetation"),
        analyses=[
            AnalysisStep(
                tool="landcover_analysis",
                reason=("Determine land-cover composition."),
            ),
            AnalysisStep(
                tool="ndvi_analysis",
                reason=("Assess vegetation characteristics."),
            ),
        ],
    )

    fake_response = type(
        "Response",
        (),
        {
            "text": expected_plan.model_dump_json(),
        },
    )()

    with patch("app.agent.gemini.create_gemini_client") as mock_client:

        mock_client.return_value.models.generate_content.return_value = fake_response

        plan = create_analysis_plan("How has urbanization affected vegetation?")

    assert plan.objective == ("Assess urbanization impact on vegetation")

    assert [step.tool for step in plan.analyses] == [
        "landcover_analysis",
        "ndvi_analysis",
    ]


def test_execute_plan_runs_all_analysis_steps():

    plan = AnalysisPlan(
        objective="Assess vegetation and land cover.",
        analyses=[
            AnalysisStep(
                tool="landcover_analysis",
                reason="Determine land-cover composition.",
            ),
            AnalysisStep(
                tool="ndvi_analysis",
                reason="Assess vegetation characteristics.",
            ),
        ],
    )

    fake_landcover_result = object()
    fake_landcover_validation = object()

    fake_ndvi_result = object()
    fake_ndvi_validation = object()

    shared_arguments = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [],
        },
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }

    with patch(
        "app.agent.planner.execute_tool",
        side_effect=[
            (
                fake_landcover_result,
                fake_landcover_validation,
            ),
            (
                fake_ndvi_result,
                fake_ndvi_validation,
            ),
        ],
    ) as mock_execute:

        results = execute_plan(
            plan,
            shared_arguments,
        )

    assert mock_execute.call_count == 2

    assert mock_execute.call_args_list[0].args == (
        "landcover_analysis",
        shared_arguments,
    )

    assert mock_execute.call_args_list[1].args == (
        "ndvi_analysis",
        shared_arguments,
    )

    assert results == [
        {
            "tool": "landcover_analysis",
            "reason": "Determine land-cover composition.",
            "result": fake_landcover_result,
            "validation": fake_landcover_validation,
        },
        {
            "tool": "ndvi_analysis",
            "reason": "Assess vegetation characteristics.",
            "result": fake_ndvi_result,
            "validation": fake_ndvi_validation,
        },
    ]


def test_plan_and_execute():

    plan = AnalysisPlan(
        objective="Assess vegetation and land cover.",
        analyses=[
            AnalysisStep(
                tool="landcover_analysis",
                reason="Determine land-cover composition.",
            ),
            AnalysisStep(
                tool="ndvi_analysis",
                reason="Assess vegetation characteristics.",
            ),
        ],
    )

    fake_results = [
        {
            "tool": "landcover_analysis",
            "reason": "Determine land-cover composition.",
            "result": object(),
            "validation": object(),
        },
        {
            "tool": "ndvi_analysis",
            "reason": "Assess vegetation characteristics.",
            "result": object(),
            "validation": object(),
        },
    ]

    shared_arguments = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [],
        },
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }

    with patch(
        "app.agent.planner.create_analysis_plan",
        return_value=plan,
    ), patch(
        "app.agent.planner.execute_plan",
        return_value=fake_results,
    ) as mock_execute:

        returned_plan, results = plan_and_execute(
            "Assess vegetation and land cover.",
            shared_arguments,
        )

    assert returned_plan == plan
    assert results == fake_results

    mock_execute.assert_called_once_with(
        plan,
        shared_arguments,
    )


def test_synthesize_analysis_results():

    plan = AnalysisPlan(
        objective="Assess vegetation and land cover.",
        analyses=[
            AnalysisStep(
                tool="ndvi_analysis",
                reason="Assess vegetation.",
            ),
            AnalysisStep(
                tool="landcover_analysis",
                reason="Assess land cover.",
            ),
        ],
    )

    ndvi_result = make_test_analysis_result_ndvi()

    ndvi_validation = make_test_validation_result()

    landcover_result = make_test_analysis_result()

    landcover_validation = make_test_validation_result()

    results = [
        {
            "tool": "ndvi_analysis",
            "reason": "Assess vegetation.",
            "result": ndvi_result,
            "validation": ndvi_validation,
        },
        {
            "tool": "landcover_analysis",
            "reason": "Assess land cover.",
            "result": landcover_result,
            "validation": landcover_validation,
        },
    ]

    fake_response = type(
        "Response",
        (),
        {"text": "The area has moderate vegetation and substantial built-up land."},
    )()

    with patch("app.agent.gemini.create_gemini_client") as mock_client:

        mock_generate = mock_client.return_value.models.generate_content

        mock_generate.return_value = fake_response

        answer = synthesize_analysis_results(
            "Assess vegetation and land cover.",
            plan,
            results,
        )

        call_kwargs = mock_generate.call_args.kwargs

        synthesis_prompt = call_kwargs["contents"]

        assert "ndvi_analysis" in synthesis_prompt
        assert "landcover_analysis" in synthesis_prompt
        # assert "0.318" in synthesis_prompt

    assert answer == ("The area has moderate vegetation and substantial built-up land.")


def test_run_planned_analysis():

    plan = AnalysisPlan(
        objective="Assess vegetation and land cover.",
        analyses=[
            AnalysisStep(
                tool="ndvi_analysis",
                reason="Assess vegetation.",
            ),
            AnalysisStep(
                tool="landcover_analysis",
                reason="Assess land cover.",
            ),
        ],
    )

    fake_results = [
        {
            "tool": "ndvi_analysis",
            "reason": "Assess vegetation.",
            "result": object(),
            "validation": object(),
        },
        {
            "tool": "landcover_analysis",
            "reason": "Assess land cover.",
            "result": object(),
            "validation": object(),
        },
    ]

    with patch(
        "app.agent.planner.create_analysis_plan",
        return_value=plan,
    ), patch(
        "app.agent.planner.execute_plan",
        return_value=fake_results,
    ), patch(
        "app.agent.planner.synthesize_analysis_results",
        return_value="Synthesized answer.",
    ):

        result = run_planned_analysis(
            "Assess vegetation and land cover.",
            {},
        )

    assert result["plan"] == plan
    assert result["results"] == fake_results
    assert result["answer"] == "Synthesized answer."
