from app.agent.executor import execute_tool
from app.agent.gemini import create_analysis_plan, synthesize_analysis_results
from app.models.plan import AnalysisPlan


def plan_and_execute(
    prompt: str,
    shared_arguments: dict,
) -> tuple:
    """
    Generate an analysis plan and execute it.
    """
    print("Planning and executing....")

    plan = create_analysis_plan(prompt)

    results = execute_plan(
        plan,
        shared_arguments,
    )

    return plan, results


def execute_plan(
    plan: AnalysisPlan,
    shared_arguments: dict,
) -> list[dict]:
    """
    Execute every analysis step in the plan.

    The planner decides WHAT to analyze.
    The coordinator supplies the shared execution context
    such as AOI and analysis dates.
    """

    print("Executing the plan...")

    results = []

    for step in plan.analyses:
        result, validation = execute_tool(
            step.tool,
            shared_arguments,
        )

        results.append(
            {
                "tool": step.tool,
                "reason": step.reason,
                "result": result,
                "validation": validation,
            }
        )

    return results


def run_planned_analysis(
    prompt: str,
    shared_arguments: dict,
):
    plan, results = plan_and_execute(
        prompt,
        shared_arguments,
    )

    answer = synthesize_analysis_results(
        prompt,
        plan,
        results,
    )

    return {
        "plan": plan,
        "results": results,
        "answer": answer,
    }
