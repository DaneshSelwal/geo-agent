from app.models.tools import (
    LandcoverToolInput,
    NDVIToolInput,
)

TOOL_SCHEMAS = {
    "ndvi_analysis": {
        "name": "ndvi_analysis",
        "description": (
            "Analyze vegetation in an area using Sentinel-2 NDVI. "
            "Use this tool when the user asks about vegetation, "
            "vegetation health, or NDVI."
        ),
        "input_model": NDVIToolInput,
    },
    "landcover_analysis": {
        "name": "landcover_analysis",
        "description": (
            "Analyze land-cover composition in an area using "
            "Google Dynamic World. Use this tool when the user "
            "asks about land-cover types such as trees, crops, "
            "water, built-up areas, or bare land."
        ),
        "input_model": LandcoverToolInput,
    },
}


def get_tool_schema(tool_name: str) -> dict:
    if tool_name not in TOOL_SCHEMAS:
        raise KeyError(f"Unknown tool: {tool_name}")

    tool = TOOL_SCHEMAS[tool_name]

    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["input_model"].model_json_schema(),
    }
