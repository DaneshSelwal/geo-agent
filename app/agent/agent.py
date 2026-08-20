# app/agent/agent.py

from app.agent.executor import execute_tool
from app.agent.gemini import (
    ask_gemini,
    extract_function_call,
    generate_replan_response,
)

MAX_REPLANS = 1

def serialize_tool_result(
    result,
    validation,
) -> dict:
    return {
        "analysis": result.model_dump(),
        "validation": validation.model_dump(),
    }


from app.agent.executor import execute_tool
from app.agent.gemini import (
    ask_gemini,
    extract_function_call,
    generate_final_response,
)


def serialize_tool_result(
    result,
    validation,
) -> dict:
    return {
        "analysis": result.model_dump(),
        "validation": validation.model_dump(),
    }


def get_tool_call_from_response(response):
    function_call = extract_function_call(response)

    if function_call is None:
        raise RuntimeError(
            "Expected Gemini to request another tool, "
            "but it returned no function call."
        )

    return function_call


def execute_function_call(function_call):
    return execute_tool(
        function_call.name,
        dict(function_call.args),
    )


def run_agent(prompt: str):
    print("1. Calling Gemini...")

    response = ask_gemini(prompt)

    print("2. Gemini responded.")

    function_call = extract_function_call(response)

    if function_call is None:
        print("3. Gemini did not request a tool.")
        return response.text

    print(f"3. Tool requested: {function_call.name}")

    print(f"4. Arguments: {function_call.args}")

    print("5. Executing tool...")

    result, validation = execute_function_call(function_call)

    print("6. Tool finished.")

    print(
        f"7. Validation: " f"{validation.quality_level} " f"(valid={validation.valid})"
    )

    tool_result = serialize_tool_result(
        result,
        validation,
    )

    if not validation.valid:
        print("8. Analysis failed validation.")

        if MAX_REPLANS <= 0:
            return {
                "status": "validation_failed",
                "analysis": tool_result,
            }

        print("9. Asking Gemini to re-plan...")

        replan_response = generate_replan_response(
            original_prompt=prompt,
            response=response,
            tool_result=tool_result,
        )

        replan_call = get_tool_call_from_response(
            replan_response
        )

        print(
            f"10. Re-plan requested: "
            f"{replan_call.name}"
        )

        print(
            f"11. Re-plan arguments: "
            f"{replan_call.args}"
        )

        print("12. Executing re-planned tool...")

        retry_result, retry_validation = (
            execute_function_call(replan_call)
        )

        print("13. Re-planned tool finished.")

        print(
            f"14. Retry validation: "
            f"{retry_validation.quality_level} "
            f"(valid={retry_validation.valid})"
        )

        retry_tool_result = serialize_tool_result(
            retry_result,
            retry_validation,
        )

        if not retry_validation.valid:
            print("15. Re-planned analysis also failed.")

            return {
                "status": "validation_failed",
                "analysis": retry_tool_result,
            }

        print("15. Re-planned analysis passed.")

        print(
            "16. Sending successful retry result "
            "back to Gemini..."
        )

        final_answer = generate_final_response(
            original_prompt=prompt,
            response=replan_response,
            tool_result=retry_tool_result,
        )

        print("17. Gemini produced final response.")

        return final_answer
    print("8. Analysis passed validation.")
    print("9. Sending result back to Gemini...")

    final_answer = generate_final_response(
        original_prompt=prompt,
        response=response,
        tool_result=tool_result,
    )

    print("10. Gemini produced final response.")

    return final_answer
