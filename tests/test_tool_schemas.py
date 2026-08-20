# tests/test_tool_schemas.py
from app.agent.tool_schemas import (
    TOOL_SCHEMAS,
    get_tool_schema,
)


def test_ndvi_tool_schema_exists():
    assert "ndvi_analysis" in TOOL_SCHEMAS


def test_landcover_tool_schema_exists():
    assert "landcover_analysis" in TOOL_SCHEMAS


def test_ndvi_tool_schema():
    schema = get_tool_schema("ndvi_analysis")

    assert schema["name"] == "ndvi_analysis"
    assert "NDVI" in schema["description"]

    properties = schema["parameters"]["properties"]

    assert "aoi" in properties
    assert "start_date" in properties
    assert "end_date" in properties
    assert "max_cloud_percentage" in properties
    assert "scale" in properties


def test_landcover_tool_schema():
    schema = get_tool_schema("landcover_analysis")

    assert schema["name"] == "landcover_analysis"
    assert "land-cover" in schema["description"]

    properties = schema["parameters"]["properties"]

    assert "aoi" in properties
    assert "start_date" in properties
    assert "end_date" in properties
    assert "scale" in properties


def test_unknown_tool_schema():
    try:
        get_tool_schema("unknown_tool")
        assert False
    except KeyError:
        pass
