from app.agent.geo import geojson_to_ee_geometry
from app.agent.tool_schemas import TOOL_SCHEMAS
from app.agent.tools import TOOLS


def execute_tool(
    tool_name: str,
    arguments: dict,
):
    """
    Validate and execute an agent-requested tool.
    """

    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    if tool_name not in TOOL_SCHEMAS:
        raise ValueError(f"No schema registered for tool: {tool_name}")

    input_model = TOOL_SCHEMAS[tool_name]["input_model"]

    validated_arguments = input_model.model_validate(arguments)

    arguments = validated_arguments.model_dump()

    arguments["aoi"] = geojson_to_ee_geometry(arguments["aoi"])

    tool = TOOLS[tool_name]

    return tool(**arguments)
