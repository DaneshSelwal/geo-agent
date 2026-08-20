from app.tools.landcover_tool import landcover_tool
from app.tools.ndvi_tool import ndvi_tool

TOOLS = {
    "ndvi_analysis": ndvi_tool,
    "landcover_analysis": landcover_tool,
}
