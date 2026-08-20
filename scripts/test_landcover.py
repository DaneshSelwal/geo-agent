import ee

from app.analysis.landcover import (
    analyze_landcover,
)
from app.config import GEE_PROJECT_ID

ee.Initialize(project=GEE_PROJECT_ID)

aoi = ee.Geometry.Rectangle(
    [
        76.80,
        28.35,
        77.20,
        28.65,
    ]
)

result = analyze_landcover(
    aoi=aoi,
    start_date="2025-01-01",
    end_date="2025-12-31",
)

print(result.model_dump_json(indent=2))
