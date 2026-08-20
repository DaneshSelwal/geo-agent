from app.agent.tools import TOOLS
from app.tools.landcover_tool import landcover_tool
from app.tools.ndvi_tool import ndvi_tool


def test_ndvi_tool_is_registered():
    assert "ndvi_analysis" in TOOLS
    assert TOOLS["ndvi_analysis"] is ndvi_tool


def test_landcover_tool_is_registered():
    assert "landcover_analysis" in TOOLS
    assert TOOLS["landcover_analysis"] is landcover_tool