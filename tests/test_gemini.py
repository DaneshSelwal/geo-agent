# tests/test_gemini.py
from app.agent.gemini import (
    get_gemini_tool_declarations,
    make_gemini_parameters,
)
from app.agent.tool_schemas import get_tool_schema


def test_gemini_parameters_remove_unsupported_fields():
    schema = get_tool_schema("ndvi_analysis")

    parameters = make_gemini_parameters(schema["parameters"])

    scale = parameters["properties"]["scale"]

    assert scale["type"] == "integer"
    assert "exclusiveMinimum" not in scale


def test_gemini_tool_declarations():
    declarations = get_gemini_tool_declarations()

    names = {declaration.name for declaration in declarations}

    assert names == {
        "ndvi_analysis",
        "landcover_analysis",
    }
