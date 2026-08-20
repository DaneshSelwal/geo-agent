import ee
from app.config import GEE_PROJECT_ID

def initialize_gee(project_id: str) -> None:
    """
    Initialize the Google Earth Engine Python API.

    Args:
        project_id: Google Cloud project ID registered for Earth Engine.
    """
    try:
        ee.Initialize(project=project_id)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project_id)

if __name__ == "__main__":
    initialize_gee(GEE_PROJECT_ID)

    result = ee.String("Hello Earth Engine").getInfo()

    print(result)
